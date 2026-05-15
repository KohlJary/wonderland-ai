"""``wonderland run-bg`` — detached background-run command.

Designed to be spawned by the TUI as a subprocess (``Popen(...,
start_new_session=True)``) so the run survives the TUI exiting.
The subprocess writes events to ``.wonderland/runs/<run_id>/events.jsonl``;
the TUI's ``SubprocessRunHandle`` tails that file when the operator
opens the live-watch screen.

Files written under ``.wonderland/runs/<run_id>/``:

  events.jsonl   — one event per line, written + flushed as each
                   event arrives. Tailable.
  status.json    — last-known run state. Updated at start, at every
                   MeetingEnded (so a quick read shows progress
                   without reparsing events), and at terminal
                   completion. Schema:
                       {"status": "running"|"complete"|"aborted"|"error",
                        "run_id": str,
                        "started_at": ISO-8601,
                        "ended_at": ISO-8601 | null,
                        "meetings_completed": int,
                        "total_cost": float,
                        "pid": int,
                        "workflow": str,
                        "directive": str}
  pid            — bare integer for cheap aliveness checks (the
                   status.json also carries the pid; this file is
                   for shell scripts / liveness probes).
  log            — stderr/stdout from the subprocess (Runner emits
                   warnings, exceptions land here too).

Signals:
  SIGTERM        — graceful abort. Runner.abort() fires; the
                   stream finishes its current event then exits.
                   Status flips to "aborted" with ended_at set.
  SIGINT         — same as SIGTERM (treat ctrl+c as graceful abort
                   when run-bg is launched directly from a terminal
                   for debugging).

Failure modes:
  - The subprocess crashes mid-run → status.json is whatever it
    was last written. The TUI's discovery code treats "pid not
    alive AND status=running" as crash and re-labels the row as
    "error" until the operator clears it.
  - Disk fills up while writing events → the writer surfaces the
    OSError to stderr (log file) and aborts the run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from wonderland.observer.event_codec import to_jsonl


def add_run_bg_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``run-bg`` subcommand on the main wonderland CLI
    parser. Called from ``cli.build_parser`` so the command shows up
    in ``wonderland --help``."""
    parser = subparsers.add_parser(
        "run-bg",
        help=(
            "Run a workflow in detached background mode. Writes "
            "events to .wonderland/runs/<run_id>/events.jsonl. "
            "Spawned by the TUI; not typically invoked directly."
        ),
        description=(
            "Detached background run. Designed to be spawned via "
            "subprocess by the Wonderland TUI; the TUI tails the "
            "events file via SubprocessRunHandle. Survives parent "
            "exit when launched with start_new_session=True."
        ),
    )
    parser.add_argument(
        "directive", help="Directive driving the run."
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="Workflow name (e.g. tdd-design, smoke-ask-user).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        required=True,
        help="Project root with .wonderland/ skeleton.",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=1.00,
        help="Dollar budget cap (default: $1.00).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional model override.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help=(
            "Override the run id (default: Runner generates a "
            "timestamp-style id). Used by the TUI to pre-create "
            "the run dir at a known path before spawning the "
            "subprocess, so the SubprocessRunHandle can tail the "
            "right files."
        ),
    )
    parser.add_argument(
        "--auto-merge",
        action="store_true",
        help=(
            "After the run completes cleanly, attempt a fast-forward "
            "merge of the run branch back into the source branch the "
            "operator was on at launch. Skipped on aborted / errored "
            "runs. Falls back to leaving the branch in place if the "
            "merge would need manual resolution."
        ),
    )
    parser.add_argument(
        "--milestone",
        type=str,
        default=None,
        help=(
            "P15 — when set, scope the workflow's seed pool to this "
            "milestone's consumes_requirements list, and prepend the "
            "milestone's goal + done_when to the entry meeting's "
            "convenor_directive. Used by tdd-design and tdd-implement "
            "to focus the team on one milestone at a time. Slug "
            "matches a milestone file at "
            "``<project>/.wonderland/milestones/milestone-NN-<slug>.md``."
        ),
    )
    parser.set_defaults(func=cmd_run_bg)


def cmd_run_bg(args: argparse.Namespace) -> int:
    """Synchronous entry point. Wraps the async driver in
    ``asyncio.run`` so the CLI dispatch table can call it
    uniformly."""
    return asyncio.run(_run_bg_async(args))


async def _run_bg_async(args: argparse.Namespace) -> int:
    """Driver: build runner, create run dir, stream events to
    events.jsonl, write status updates, handle signals."""
    from wonderland.observer import LiveRunHandle
    from wonderland.observer.events import (
        MeetingEnded,
        RunEnded,
    )
    from wonderland.runner import Runner
    from wonderland.workflow import load_workflow

    project_root: Path = args.project_root.resolve()
    if not project_root.exists():
        print(
            f"error: project root {project_root} does not exist",
            file=sys.stderr,
        )
        return 1

    try:
        workflow = load_workflow(args.workflow)
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to load workflow: {exc}", file=sys.stderr)
        return 1

    try:
        runner = await Runner.make_full_cast(
            project_root,
            budget_dollars=args.budget,
            model=args.model,
            run_id=args.run_id,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to construct runner: {exc}", file=sys.stderr)
        return 1

    # Set up the run directory + open the events file. Note we
    # create the dir under .wonderland/runs/ (not the project root
    # directly) so multiple background runs against one project get
    # their own subdirectories — a future-friendly shape even
    # though the current cap is one-at-a-time.
    run_dir = project_root / ".wonderland" / "runs" / runner.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    events_path = run_dir / "events.jsonl"
    status_path = run_dir / "status.json"
    pid_path = run_dir / "pid"

    pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")

    handle = LiveRunHandle(
        runner=runner,
        workflow=workflow,
        directive=args.directive,
        milestone_slug=getattr(args, "milestone", None),
    )
    # Wire the disk-mediated operator-question handler. The TUI's
    # background-run poller (in App._poll_questions_for_run) picks
    # up pending_question.json and pushes the AskUserModal; the
    # handler here writes the question, blocks reading
    # pending_answer.json, returns the operator's reply (or sentinel
    # on timeout when no TUI is attached / operator left).
    question_path = run_dir / "pending_question.json"
    answer_path = run_dir / "pending_answer.json"

    async def _ask_operator(question_utterance) -> str | None:
        return await _disk_mediated_question(
            question_utterance,
            question_path=question_path,
            answer_path=answer_path,
        )

    handle.set_user_question_handler(_ask_operator)

    # Per-run git branch. Captures the source branch so we can
    # attempt a fast-forward merge back at the end (when --auto-merge
    # is set). Open before status.json so source_branch can ride
    # along on the status record. open_run_branch silently no-ops
    # when git isn't available; the run continues without
    # branch isolation in that case.
    from wonderland.git_run import open_run_branch

    source_branch = open_run_branch(project_root, runner.run_id)

    state = _BackgroundState(
        run_id=runner.run_id,
        started_at=datetime.now(tz=timezone.utc),
        workflow=args.workflow,
        directive=args.directive,
        meetings_completed=0,
        total_cost=0.0,
        source_branch=source_branch,
        auto_merge=bool(args.auto_merge),
    )
    _write_status(status_path, state, status="running")

    # Signal handling — SIGTERM + SIGINT both call runner.abort.
    # Async-friendly: use the loop's add_signal_handler so the
    # current event-loop iteration finishes before the abort
    # propagates through the stream.
    loop = asyncio.get_running_loop()
    aborted = asyncio.Event()

    def _handle_signal() -> None:
        if not aborted.is_set():
            aborted.set()
            try:
                runner.abort(reason="background runner received signal")
            except Exception:  # noqa: BLE001
                # Abort is best-effort — runner may already be torn
                # down. Log to stderr and let the stream exhaust.
                print(
                    "abort signal: runner.abort raised; continuing "
                    "to drain stream",
                    file=sys.stderr,
                )

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except (NotImplementedError, RuntimeError):
            # Some sandboxes (Windows) don't support add_signal_handler.
            # Fall back to the synchronous handler — fires on the
            # main thread but at the next event-loop iteration.
            signal.signal(sig, lambda *_: _handle_signal())

    exit_code = 0
    final_status = "complete"
    with events_path.open("a", encoding="utf-8") as events_file:
        try:
            async for event in handle.stream_events():
                _write_event(events_file, event)
                if isinstance(event, MeetingEnded):
                    state.meetings_completed += 1
                    state.total_cost += event.cost_delta
                    _write_status(status_path, state, status="running")
                elif isinstance(event, RunEnded):
                    state.total_cost = event.summary.total_cost
                    final_status = (
                        event.summary.outcome.lower()
                        if event.summary.outcome
                        else "complete"
                    )
                    if final_status == "complete":
                        pass
                    elif final_status in ("aborted", "global_budget", "timeout"):
                        # Map runner-level outcomes onto the
                        # status.json terminal vocabulary. Aborted
                        # gets its own status; budget/timeout fold
                        # into "aborted" since for the dashboard
                        # they're equivalent (run didn't finish
                        # cleanly, telemetry is partial).
                        final_status = "aborted"
        except asyncio.CancelledError:
            final_status = "aborted"
            raise
        except Exception as exc:  # noqa: BLE001
            print(
                f"error: stream raised — {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            final_status = "error"
            exit_code = 1
        finally:
            state.ended_at = datetime.now(tz=timezone.utc)
            _write_status(status_path, state, status=final_status)

    # Post-run git: commit working-tree changes onto the run branch,
    # then optionally fast-forward merge back to source. Only runs
    # when a source branch was successfully captured at start — if
    # git wasn't available, both calls no-op.
    if source_branch is not None:
        from wonderland.git_run import attempt_merge, commit_run

        commit_summary = (
            f"workflow: {args.workflow}\n"
            f"directive: {args.directive[:200].strip()}"
        )
        commit_run(project_root, runner.run_id, commit_summary)

        if args.auto_merge and final_status == "complete":
            merge_result = attempt_merge(project_root, source_branch)
            state.merge_outcome = merge_result.outcome.value
            state.merge_detail = merge_result.detail
            _write_status(status_path, state, status=final_status)

    return exit_code


# Default operator-question wait window (10 minutes). After this
# the subprocess gives up waiting and returns the sentinel reply
# so the run can continue. Generous enough to cover an operator
# stepping away briefly; short enough that a run doesn't strand
# indefinitely when nobody's at the keyboard.
_DEFAULT_QUESTION_TIMEOUT_SECONDS = 600.0
# Poll interval for the answer file. 0.5s is fast enough that the
# operator's modal-dismiss → answer-file-write → subprocess-pickup
# round-trip feels responsive (~1s total), while keeping CPU
# usage trivial.
_QUESTION_POLL_SECONDS = 0.5


async def _disk_mediated_question(
    question_utterance,
    *,
    question_path: Path,
    answer_path: Path,
    timeout_seconds: float = _DEFAULT_QUESTION_TIMEOUT_SECONDS,
) -> str | None:
    """Background-run operator-question handler. Writes
    ``pending_question.json`` and blocks waiting for the App-side
    poller to write ``pending_answer.json``. Returns the operator's
    reply text, or None on skip / timeout (the runner's watcher
    publishes a sentinel observation on None).

    Each call gets a fresh ``question_id`` (uuid4) so the
    subprocess can disambiguate its own answer from any stale
    answer file left over from a prior question. Both files are
    cleaned up on the way out — answer file is deleted (it's
    consumed) and question file is deleted (the question is
    resolved).

    On timeout the subprocess writes its own sentinel-equivalent
    (None) so the run continues. Operator who shows up after the
    timeout sees the run already moved on; they can re-queue if
    they think the team made the wrong call.
    """
    import uuid

    question_id = uuid.uuid4().hex
    options: list[str] = []
    for artifact in question_utterance.content.artifacts:
        if artifact.kind == "operator_question_options":
            raw = artifact.payload.get("options", [])
            if isinstance(raw, list):
                options = [str(o) for o in raw if o]
            break

    question_data = {
        "question_id": question_id,
        "asking_agent": question_utterance.speaker.name,
        "question": question_utterance.content.body,
        "options": options,
    }
    try:
        question_path.write_text(
            json.dumps(question_data), encoding="utf-8"
        )
    except OSError as exc:
        print(
            f"warn: failed to write pending_question.json: {exc}",
            file=sys.stderr,
        )
        return None

    deadline = asyncio.get_running_loop().time() + timeout_seconds
    answer: str | None = None
    try:
        while asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(_QUESTION_POLL_SECONDS)
            if not answer_path.is_file():
                continue
            try:
                data = json.loads(
                    answer_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("question_id") != question_id:
                # Stale answer file from a prior question. Clean
                # it up so it doesn't trip the next iteration.
                try:
                    answer_path.unlink()
                except OSError:
                    pass
                continue
            raw_answer = data.get("answer")
            if isinstance(raw_answer, str):
                answer = raw_answer
            break
    finally:
        for path in (question_path, answer_path):
            try:
                path.unlink()
            except OSError:
                pass
    return answer


class _BackgroundState:
    """Mutable state tracked across the run for status.json updates.
    Plain attribute container — not a dataclass because we mutate
    fields incrementally during the stream."""

    __slots__ = (
        "run_id",
        "started_at",
        "ended_at",
        "workflow",
        "directive",
        "meetings_completed",
        "total_cost",
        "source_branch",
        "auto_merge",
        "merge_outcome",
        "merge_detail",
    )

    def __init__(
        self,
        *,
        run_id: str,
        started_at: datetime,
        workflow: str,
        directive: str,
        meetings_completed: int,
        total_cost: float,
        source_branch: str | None = None,
        auto_merge: bool = False,
    ) -> None:
        self.run_id = run_id
        self.started_at = started_at
        self.ended_at: datetime | None = None
        self.workflow = workflow
        self.directive = directive
        self.meetings_completed = meetings_completed
        self.total_cost = total_cost
        self.source_branch = source_branch
        self.auto_merge = auto_merge
        # Set after the post-run merge attempt; None until then.
        self.merge_outcome: str | None = None
        self.merge_detail: str | None = None


def _write_status(
    path: Path, state: _BackgroundState, *, status: str
) -> None:
    """Atomic-ish status write: dump dict + replace the file. Not a
    full atomic replace via tempfile + rename (overkill for a
    single-line status), but JSON encoders are buffered enough that
    a partial read at the wrong moment is rare in practice. If
    that turns out to bite, swap to write-temp-then-rename."""
    data: dict[str, Any] = {
        "status": status,
        "run_id": state.run_id,
        "started_at": state.started_at.isoformat(),
        "ended_at": (
            state.ended_at.isoformat() if state.ended_at else None
        ),
        "meetings_completed": state.meetings_completed,
        "total_cost": state.total_cost,
        "pid": os.getpid(),
        "workflow": state.workflow,
        "directive": state.directive,
        "source_branch": state.source_branch,
        "auto_merge": state.auto_merge,
        "merge_outcome": state.merge_outcome,
        "merge_detail": state.merge_detail,
    }
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")


def _write_event(file: TextIO, event: Any) -> None:
    """Encode + append + flush. Flush is what makes the file
    tailable — without it the OS buffer holds events until the
    process exits, defeating the live-watch purpose."""
    try:
        line = to_jsonl(event)
    except (TypeError, ValueError) as exc:
        # Codec doesn't know this event type. Log + skip; the run
        # itself isn't broken, just one event got dropped.
        print(
            f"warn: event_codec.to_jsonl({type(event).__name__}): "
            f"{exc}",
            file=sys.stderr,
        )
        return
    file.write(line)
    file.write("\n")
    file.flush()


__all__ = [
    "add_run_bg_subparser",
    "cmd_run_bg",
]
