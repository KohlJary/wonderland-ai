"""Tests for ``observer.subprocess.SubprocessRunHandle`` — the
read-only handle the TUI uses to observe a detached background run
by tailing its events.jsonl + status.json."""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from wonderland.observer.event_codec import to_jsonl
from wonderland.observer.events import (
    MeetingStarted,
    RunEnded,
    RunStarted,
)
from wonderland.observer.interface import RunMeeting, RunSummary
from wonderland.observer.subprocess import SubprocessRunHandle


T0 = datetime(2026, 5, 10, 14, 0, 0, tzinfo=timezone.utc)


def _make_run_dir(tmp_path: Path, run_id: str = "run-x") -> Path:
    run_dir = tmp_path / "alpha" / ".wonderland" / "runs" / run_id
    run_dir.mkdir(parents=True)
    return run_dir


def _write_status(
    run_dir: Path, *, status: str, run_id: str = "run-x"
) -> None:
    (run_dir / "status.json").write_text(json.dumps({
        "status": status,
        "run_id": run_id,
        "started_at": T0.isoformat(),
        "ended_at": None if status == "running" else T0.isoformat(),
        "meetings_completed": 0,
        "total_cost": 0.42,
        "pid": os.getpid(),
        "workflow": "tdd-design",
        "directive": "ship the thing",
    }) + "\n", encoding="utf-8")


def _summary() -> RunSummary:
    return RunSummary(
        run_id="run-x",
        workflow_name="tdd-design",
        directive="ship",
        project_root=Path("/tmp/proj"),
        started_at=T0,
        ended_at=None,
        total_cost=0.0,
        total_calls=0,
        outcome=None,
    )


@pytest.mark.asyncio
async def test_streams_events_and_exits_on_terminal_status(
    tmp_path: Path,
) -> None:
    """Pre-populated events.jsonl + status=complete: stream yields
    each event in order then exits cleanly."""
    run_dir = _make_run_dir(tmp_path)
    events = [
        RunStarted(timestamp=T0, summary=_summary()),
        RunEnded(timestamp=T0, summary=_summary()),
    ]
    (run_dir / "events.jsonl").write_text(
        "\n".join(to_jsonl(e) for e in events) + "\n",
        encoding="utf-8",
    )
    (run_dir / "pid").write_text(f"{os.getpid()}\n")
    _write_status(run_dir, status="complete")

    handle = SubprocessRunHandle(run_dir)
    yielded: list = []
    async for event in handle.stream_events():
        yielded.append(event)

    assert len(yielded) == 2
    assert isinstance(yielded[0], RunStarted)
    assert isinstance(yielded[1], RunEnded)


@pytest.mark.asyncio
async def test_tails_new_events_appended_mid_stream(
    tmp_path: Path,
) -> None:
    """While the run is still running, the handle polls for new
    events appended after EOF. Append-then-flip-status is the
    background runner's pattern."""
    run_dir = _make_run_dir(tmp_path)
    events_path = run_dir / "events.jsonl"
    events_path.write_text("", encoding="utf-8")
    (run_dir / "pid").write_text(f"{os.getpid()}\n")
    _write_status(run_dir, status="running")

    handle = SubprocessRunHandle(run_dir)

    async def append_then_finish() -> None:
        # Give the consumer a moment to land in the poll loop, then
        # append two events and flip status to complete.
        await asyncio.sleep(0.2)
        with events_path.open("a", encoding="utf-8") as f:
            f.write(to_jsonl(
                RunStarted(timestamp=T0, summary=_summary())
            ) + "\n")
            f.flush()
        await asyncio.sleep(0.3)
        with events_path.open("a", encoding="utf-8") as f:
            f.write(to_jsonl(
                MeetingStarted(
                    timestamp=T0,
                    meeting=RunMeeting(
                        id="m1",
                        label="M1",
                        name=None,
                        started_at=T0,
                        ended_at=None,
                        outcome=None,
                        elapsed_seconds=None,
                        calls=0,
                        cost=0.0,
                    ),
                    thread_id="m1",
                )
            ) + "\n")
            f.flush()
        await asyncio.sleep(0.3)
        with events_path.open("a", encoding="utf-8") as f:
            f.write(to_jsonl(
                RunEnded(timestamp=T0, summary=_summary())
            ) + "\n")
            f.flush()
        _write_status(run_dir, status="complete")

    appender = asyncio.create_task(append_then_finish())
    yielded: list = []
    async for event in handle.stream_events():
        yielded.append(event)
    await appender

    assert len(yielded) == 3
    assert isinstance(yielded[0], RunStarted)
    assert isinstance(yielded[1], MeetingStarted)
    assert isinstance(yielded[2], RunEnded)


def test_status_and_pid_reads(tmp_path: Path) -> None:
    """summary() / pid() / status() / is_alive() exercise the
    metadata-on-disk layer without touching the event stream."""
    run_dir = _make_run_dir(tmp_path)
    (run_dir / "pid").write_text(f"{os.getpid()}\n")
    _write_status(run_dir, status="running")

    handle = SubprocessRunHandle(run_dir)
    assert handle.pid() == os.getpid()
    assert handle.is_alive() is True  # The test process is alive!
    summary = handle.summary()
    assert summary.run_id == "run-x"
    assert summary.workflow_name == "tdd-design"
    assert summary.outcome is None  # Status=running → outcome unset

    _write_status(run_dir, status="complete")
    summary2 = handle.summary()
    assert summary2.outcome == "complete"


def test_is_alive_false_when_pid_dead(tmp_path: Path) -> None:
    """Crash detection: pid points at a nonexistent process →
    is_alive returns False. A status=running file paired with
    is_alive=False is how the TUI surfaces "subprocess crashed"."""
    run_dir = _make_run_dir(tmp_path)
    # Use a pid we can be confident is dead (negative ints reject
    # via OSError, but small high pids that aren't allocated work).
    # Spawn-and-reap a quick child to get a guaranteed-dead pid.
    fake_pid = os.fork() if hasattr(os, "fork") else 1_000_000
    if fake_pid == 0:
        # Child: exit immediately.
        os._exit(0)
    if hasattr(os, "fork"):
        # Reap the child so its pid is fully released.
        os.waitpid(fake_pid, 0)
        # Brief settle so the pid table updates.
        time.sleep(0.05)
    (run_dir / "pid").write_text(f"{fake_pid}\n")
    _write_status(run_dir, status="running")

    handle = SubprocessRunHandle(run_dir)
    assert handle.is_alive() is False


def test_decode_skips_malformed_lines(tmp_path: Path) -> None:
    """One bad JSONL line shouldn't poison the rest of the stream."""
    run_dir = _make_run_dir(tmp_path)
    (run_dir / "pid").write_text(f"{os.getpid()}\n")
    _write_status(run_dir, status="complete")
    good = to_jsonl(RunStarted(timestamp=T0, summary=_summary()))
    bad = '{"kind": "GremlinSpotted", "data": {}}'
    also_good = to_jsonl(RunEnded(timestamp=T0, summary=_summary()))
    (run_dir / "events.jsonl").write_text(
        f"{good}\n{bad}\n{also_good}\n",
        encoding="utf-8",
    )

    handle = SubprocessRunHandle(run_dir)
    yielded: list = []
    asyncio.run(_drain(handle, yielded))

    assert len(yielded) == 2
    assert isinstance(yielded[0], RunStarted)
    assert isinstance(yielded[1], RunEnded)


async def _drain(handle: SubprocessRunHandle, sink: list) -> None:
    async for event in handle.stream_events():
        sink.append(event)
