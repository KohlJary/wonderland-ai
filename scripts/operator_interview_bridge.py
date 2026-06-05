#!/usr/bin/env python3
"""Watch a wonderland run dir for interview prompts + emit event lines.

Companion to ``wonderland run-bg`` when the operator role is being
played by Claude Code in a chat session (rather than the TUI's
InterviewModal). Each interview cycle:

    1. interviewer ships ``interview_question_batch``
    2. substrate writes ``pending_interview.json`` into the run dir
    3. THIS SCRIPT detects the file's appearance and emits a single
       line to stdout encoding the questions as JSON
    4. Claude Code reads the line, asks the operator (user) the
       questions, writes ``pending_interview_answers.json`` back
    5. substrate consumes the answers + deletes both files
    6. loop back to step 1 (until ``RunEnded`` appears in events.jsonl)

Output format (one JSON object per line, line-buffered):

    {"kind": "interview_prompt", "run_id": "...", "questions": [...], "interviewer": "..."}
    {"kind": "run_ended", "outcome": "COMPLETE", "total_cost": 0.4321, "total_calls": 19}
    {"kind": "error", "message": "..."}

Used as the Monitor body in chat sessions; stdout lines become
notifications Claude Code sees in real time. Exits 0 on RunEnded,
non-zero on internal error.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PENDING_QUESTION = "pending_interview.json"
PENDING_ANSWERS = "pending_interview_answers.json"
EVENTS = "events.jsonl"
POLL_SECONDS = 0.5


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _run_ended(events_path: Path, seen_offset: int) -> tuple[dict | None, int]:
    """Return (run_ended_event_data, new_offset) if RunEnded has appeared."""
    if not events_path.exists():
        return None, seen_offset
    size = events_path.stat().st_size
    if size <= seen_offset:
        return None, seen_offset
    with events_path.open("r") as f:
        f.seek(seen_offset)
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("kind") == "RunEnded":
                return event.get("data", {}).get("summary", {}), size
    return None, size


def watch(run_dir: Path) -> int:
    pending_path = run_dir / PENDING_QUESTION
    answers_path = run_dir / PENDING_ANSWERS
    events_path = run_dir / EVENTS

    last_emitted_mtime: float | None = None
    events_offset = 0

    while True:
        # Has the run ended?
        ended_summary, events_offset = _run_ended(events_path, events_offset)
        if ended_summary is not None:
            _emit({"kind": "run_ended", **ended_summary})
            return 0

        # New interview prompt?
        if pending_path.exists():
            mtime = pending_path.stat().st_mtime
            if last_emitted_mtime is None or mtime > last_emitted_mtime:
                # Wait briefly for the writer to finish flushing.
                time.sleep(0.1)
                try:
                    payload = json.loads(pending_path.read_text())
                except (json.JSONDecodeError, OSError) as exc:
                    _emit({"kind": "error", "message": f"failed to read {pending_path}: {exc}"})
                    time.sleep(POLL_SECONDS)
                    continue
                _emit(
                    {
                        "kind": "interview_prompt",
                        "run_id": run_dir.name,
                        "pending_path": str(pending_path),
                        "answers_path": str(answers_path),
                        "interviewer": payload.get("interviewer") or payload.get("agent"),
                        "interview_id": payload.get("interview_id"),
                        "questions": payload.get("questions", []),
                        "context": {k: v for k, v in payload.items() if k not in ("questions",)},
                    }
                )
                last_emitted_mtime = mtime

        time.sleep(POLL_SECONDS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Path to .wonderland/runs/<run_id>/")
    args = parser.parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        # Wait for it to appear (run-bg may not have created it yet).
        deadline = time.time() + 30.0
        while time.time() < deadline and not run_dir.exists():
            time.sleep(POLL_SECONDS)
        if not run_dir.exists():
            _emit({"kind": "error", "message": f"run dir never appeared: {run_dir}"})
            return 2
    return watch(run_dir)


if __name__ == "__main__":
    sys.exit(main())
