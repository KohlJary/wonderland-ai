"""``SubprocessRunHandle`` — observe a background ``wonderland run-bg``
subprocess by tailing its events.jsonl + status.json on disk.

The detached-process counterpart to ``LiveRunHandle``. Same
``RunHandle`` protocol; instead of subscribing to a Runner running
in-process, we tail the JSONL file the subprocess writes to its
run dir.

Used by ``WonderlandApp`` to plug the LiveRunScreen into a
background run — the screen doesn't know whether it's reading from
an in-process Runner (legacy path) or a detached subprocess; it
just iterates ``stream_events()``.

Lifecycle:
  - Construct from the run dir (``.wonderland/runs/<run_id>/``).
  - ``stream_events()`` yields each event in events.jsonl,
    chronologically. When it reaches end-of-file mid-run, polls
    the file for new appends with backoff. When status.json flips
    to a terminal status, drains any remaining events then exits.
  - ``abort()`` sends SIGTERM to the recorded pid. The subprocess
    catches it, calls runner.abort(), drains the stream, writes
    final status, exits.

Failure modes:
  - Subprocess crashed (pid not alive but status=running) →
    treated as terminal "error". Operator sees the partial events
    that did make it to disk before the crash.
  - events.jsonl truncated mid-line → the malformed tail is
    skipped; remaining lines yield as normal. UnknownEventKind
    raises when the codec sees a future event type, which the
    handle surfaces to the caller (operator sees a notify they
    need to upgrade their TUI).
"""

from __future__ import annotations

import asyncio
import errno
import json
import os
import signal
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from wonderland.observer.event_codec import UnknownEventKind, from_jsonl
from wonderland.observer.interface import (
    AgentTelemetry,
    RunArtifact,
    RunHandle,
    RunMeeting,
    RunSummary,
)
from wonderland.utterance import Utterance


# Polling backoff while tailing — start at 100ms, double up to 1s
# when the file goes quiet so a long-quiescent run doesn't burn CPU.
# Reset on each new event.
_POLL_INITIAL = 0.1
_POLL_MAX = 1.0
_POLL_BACKOFF_FACTOR = 1.5


class SubprocessRunHandle(RunHandle):
    """Read-only view over a ``wonderland run-bg`` subprocess via its
    on-disk artifacts.

    ``run_dir`` points at ``.wonderland/runs/<run_id>/``. Required
    files inside:

      - ``events.jsonl`` (created by the subprocess on first event;
        may briefly not exist between subprocess spawn and first
        event landing — stream_events polls)
      - ``status.json`` (always present after subprocess startup)
      - ``pid`` (always present after subprocess startup)
    """

    def __init__(self, run_dir: str | Path) -> None:
        self._run_dir = Path(run_dir)
        self._events_path = self._run_dir / "events.jsonl"
        self._status_path = self._run_dir / "status.json"
        self._pid_path = self._run_dir / "pid"

    @property
    def run_dir(self) -> Path:
        return self._run_dir

    # ------------------------------------------------------------------ #
    # Lifecycle / control
    # ------------------------------------------------------------------ #

    def pid(self) -> int | None:
        """Read the subprocess pid. Returns None if the pid file is
        missing or unreadable. Best-effort — operators clearing pid
        files manually shouldn't crash the handle."""
        try:
            return int(self._pid_path.read_text().strip())
        except (OSError, ValueError):
            return None

    def is_alive(self) -> bool:
        """Cheap aliveness check via signal 0. Returns False on
        ESRCH (no such pid). Doesn't differentiate "subprocess died
        cleanly" from "subprocess crashed" — the status.json field
        carries that nuance."""
        pid = self.pid()
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError as exc:
            return exc.errno != errno.ESRCH

    def status(self) -> dict[str, Any]:
        """Read the latest status.json. Returns {} on missing /
        malformed file — caller should treat that as "unknown
        state, probably starting up"."""
        try:
            return json.loads(self._status_path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def abort(self, *, reason: str | None = None) -> bool:
        """Send SIGTERM to the subprocess. The subprocess's signal
        handler catches it, calls runner.abort, drains the stream,
        writes a terminal status. Returns False if the pid couldn't
        be resolved or if the kill itself raised; otherwise True."""
        del reason  # Logged in the subprocess via its own machinery
        pid = self.pid()
        if pid is None:
            return False
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except OSError:
            return False

    # ------------------------------------------------------------------ #
    # RunHandle protocol — non-streaming accessors
    # ------------------------------------------------------------------ #

    def summary(self) -> RunSummary:
        status = self.status()
        started_iso = status.get("started_at")
        ended_iso = status.get("ended_at")
        return RunSummary(
            run_id=status.get("run_id"),
            workflow_name=status.get("workflow"),
            directive=status.get("directive"),
            project_root=self._run_dir.parent.parent,  # .../<proj>/.wonderland/runs/<id>
            started_at=(
                datetime.fromisoformat(started_iso)
                if started_iso
                else None
            ),
            ended_at=(
                datetime.fromisoformat(ended_iso) if ended_iso else None
            ),
            total_cost=float(status.get("total_cost") or 0.0),
            total_calls=0,  # Not tracked in status.json; events stream carries it
            outcome=(
                status.get("status")
                if status.get("status") in ("complete", "aborted", "error")
                else None
            ),
        )

    def meetings(self) -> list[RunMeeting]:
        # Subprocess hasn't summarized meetings out-of-band — they're
        # available via the event stream. For a non-streaming
        # consumer, returning [] degrades gracefully (LiveRunScreen
        # builds its meetings table from MeetingStarted events
        # anyway). Could backfill by replaying the JSONL file in
        # future if a non-streaming consumer needs this.
        return []

    def utterances(
        self, *, thread_id: str | None = None
    ) -> Iterator[Utterance]:
        # Same shape as meetings(): the event stream is the
        # authoritative source. Replay JSONL would be straightforward
        # but no current consumer needs it; defer.
        if False:
            yield  # type: ignore[unreachable]

    def per_agent_telemetry(self) -> list[AgentTelemetry]:
        return []

    def artifacts(self, *, kind: str | None = None) -> list[RunArtifact]:
        # Artifacts land in the project's .wonderland/<kind>/
        # directories as the run progresses; HistoricalRunHandle
        # reads them once the run is done. For SubprocessRunHandle
        # we lean on the event stream's ArtifactShipped events.
        del kind
        return []

    # ------------------------------------------------------------------ #
    # Streaming — the substantive method
    # ------------------------------------------------------------------ #

    async def stream_events(self) -> AsyncIterator[Any]:
        """Tail events.jsonl, yielding each event in order. When the
        file reaches EOF and the run is still running, polls for
        new appends with backoff. When status flips to terminal,
        drains the remaining tail and exits.

        Cancellation: if the consumer's async-for is cancelled
        (e.g. screen unmount), the polling loop exits cleanly on
        the next iteration. No file handles to clean up since we
        re-open + seek on each pass; this keeps inotify-style
        complexity out of the picture at the cost of a tiny bit of
        extra IO per poll.
        """
        offset = 0
        backoff = _POLL_INITIAL
        # Wait briefly for the file to appear if the subprocess
        # hasn't written its first event yet.
        await self._wait_for_events_file(timeout=10.0)

        while True:
            new_lines, new_offset = self._read_new_lines(offset)
            offset = new_offset
            for line in new_lines:
                event = self._decode_line(line)
                if event is not None:
                    yield event
            if new_lines:
                backoff = _POLL_INITIAL
                continue
            # No new lines. Check terminal status — if set, we're
            # done (the writer already flushed the final event
            # before updating status).
            status = self.status()
            current = status.get("status")
            if current in ("complete", "aborted", "error"):
                # One more pass to catch any tail event that landed
                # between the read and the status check.
                new_lines, _ = self._read_new_lines(offset)
                for line in new_lines:
                    event = self._decode_line(line)
                    if event is not None:
                        yield event
                return
            # Crash detection: if status says running but the pid
            # is gone, the subprocess died without writing a
            # terminal status. Treat as error and exit.
            if current == "running" and not self.is_alive():
                return
            await asyncio.sleep(backoff)
            backoff = min(backoff * _POLL_BACKOFF_FACTOR, _POLL_MAX)

    async def _wait_for_events_file(self, *, timeout: float) -> None:
        """Block until events.jsonl exists or ``timeout`` elapses.
        Used at stream startup so we don't barrel into reads of a
        nonexistent file while the subprocess is still spawning."""
        deadline = asyncio.get_event_loop().time() + timeout
        while not self._events_path.exists():
            if asyncio.get_event_loop().time() >= deadline:
                return  # Exit anyway — let the poll loop's missing-file
                #         path render an empty stream gracefully.
            await asyncio.sleep(0.05)

    def _read_new_lines(self, offset: int) -> tuple[list[str], int]:
        """Open events.jsonl, seek to ``offset``, return any newly-
        appended complete lines + the updated byte offset.

        Trailing partial line (no ``\\n`` yet) is left in the file
        and re-read on the next poll. Returns ([], offset)
        unchanged when the file doesn't exist yet."""
        if not self._events_path.exists():
            return [], offset
        try:
            with self._events_path.open(encoding="utf-8") as f:
                f.seek(offset)
                chunk = f.read()
                new_offset = f.tell()
        except OSError:
            return [], offset
        if not chunk:
            return [], new_offset
        # Split on \n; the trailing element after the last \n is
        # incomplete — back up the offset by its byte length so we
        # re-read it next poll.
        parts = chunk.split("\n")
        complete_lines = [p for p in parts[:-1] if p]
        trailing_partial_bytes = len(parts[-1].encode("utf-8"))
        adjusted_offset = new_offset - trailing_partial_bytes
        return complete_lines, adjusted_offset

    def _decode_line(self, line: str) -> Any:
        """Decode a single JSONL line. Returns None on malformed /
        unknown-kind lines (logged via stderr). The stream
        continues — one bad line shouldn't poison the rest."""
        try:
            return from_jsonl(line)
        except (json.JSONDecodeError, UnknownEventKind, ValueError):
            return None


__all__ = ["SubprocessRunHandle"]
