#!/usr/bin/env python3
"""Watch a project's runs dir + emit one line per RunEnded event.

Long-running companion to ``wonderland run-bg`` when the operator
role is being played by Claude Code: instead of spawning a blocking
``until grep RunEnded`` watcher per phase, this script tails every
run dir under a project, detects new runs as they appear, and emits
one notification line per RunEnded with a structured summary.

Companion to ``operator_interview_bridge.py`` — that script handles
the per-interview prompt/answer cycle within a single discovery run;
this script handles the cross-run "is the phase done yet" signal.

Output format (one line per event, line-buffered):

    RUN_STARTED  <run_id>  workflow=<name>
    RUN_ENDED    <run_id>  workflow=<name>  outcome=<o>  cost=$<x>  calls=<n>  duration=<m>min
    INTERVIEW    <run_id>  interviewer=<who>  label=<I1|I2|I3>  questions=<n>
    ERROR        <run_id>  <message>

Designed to run via Claude Code's Monitor tool (each stdout line
becomes a notification). Persistent — runs until killed via TaskStop
or session end.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

POLL_SECONDS = 2.0
EVENTS = "events.jsonl"
PENDING_INTERVIEW = "pending_interview.json"


def _emit(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _scan_runs(runs_dir: Path) -> list[Path]:
    if not runs_dir.is_dir():
        return []
    return sorted(p for p in runs_dir.iterdir() if p.is_dir())


def _ended_summary(events_path: Path, offset: int) -> tuple[dict | None, int, dict | None]:
    """Read events.jsonl from offset; return (run_ended_summary, new_offset, run_started_summary).
    Either summary may be None if not yet present."""
    if not events_path.exists():
        return None, offset, None
    size = events_path.stat().st_size
    if size <= offset:
        return None, offset, None
    ended = None
    started = None
    try:
        with events_path.open("r") as f:
            f.seek(offset)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("kind") == "RunStarted":
                    started = event.get("data", {}).get("summary", {})
                elif event.get("kind") == "RunEnded":
                    ended = event.get("data", {}).get("summary", {})
    except OSError:
        pass
    return ended, size, started


def _interview_summary(pending_path: Path, last_mtime: float | None) -> tuple[dict | None, float | None]:
    if not pending_path.exists():
        return None, last_mtime
    mtime = pending_path.stat().st_mtime
    if last_mtime is not None and mtime <= last_mtime:
        return None, last_mtime
    time.sleep(0.1)  # let the writer flush
    try:
        payload = json.loads(pending_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None, last_mtime
    return payload, mtime


def watch(project_root: Path) -> int:
    runs_dir = project_root / ".wonderland" / "runs"
    # per-run state: {run_id: {"events_offset": int, "interview_mtime": float|None, "started": bool, "ended": bool}}
    state: dict[str, dict] = {}

    _emit(f"WATCH_START  project={project_root.name}")
    while True:
        for run_dir in _scan_runs(runs_dir):
            run_id = run_dir.name
            st = state.setdefault(
                run_id,
                {"events_offset": 0, "interview_mtime": None, "started": False, "ended": False},
            )
            if st["ended"]:
                continue
            ended, new_offset, started = _ended_summary(run_dir / EVENTS, st["events_offset"])
            st["events_offset"] = new_offset
            if started and not st["started"]:
                st["started"] = True
                _emit(f"RUN_STARTED  {run_id}  workflow={started.get('workflow_name','?')}")
            interview, new_mtime = _interview_summary(run_dir / PENDING_INTERVIEW, st["interview_mtime"])
            if interview:
                st["interview_mtime"] = new_mtime
                _emit(
                    f"INTERVIEW    {run_id}  interviewer={interview.get('interviewer','?')}"
                    f"  label={interview.get('label','?')}"
                    f"  questions={len(interview.get('questions', []))}"
                    f"  batch={interview.get('batch_id','?')[:8]}"
                )
            if ended:
                import datetime
                try:
                    start_dt = datetime.datetime.fromisoformat(ended["started_at"])
                    end_dt = datetime.datetime.fromisoformat(ended["ended_at"])
                    duration_min = (end_dt - start_dt).total_seconds() / 60.0
                except (KeyError, ValueError):
                    duration_min = 0.0
                _emit(
                    f"RUN_ENDED    {run_id}  workflow={ended.get('workflow_name','?')}"
                    f"  outcome={ended.get('outcome','?')}"
                    f"  cost=${ended.get('total_cost', 0):.4f}"
                    f"  calls={ended.get('total_calls', 0)}"
                    f"  duration={duration_min:.1f}min"
                )
                st["ended"] = True
        time.sleep(POLL_SECONDS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.is_dir():
        _emit(f"ERROR  project root not found: {project_root}")
        return 2
    return watch(project_root)


if __name__ == "__main__":
    sys.exit(main())
