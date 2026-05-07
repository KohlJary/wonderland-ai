"""Print a quick summary of a run snapshot via HistoricalRunHandle.

Usage:
    uv run python scripts/inspect_run.py analyses/data/029-substrate-convergence/v6/

Renders run summary, per-meeting breakdown, per-agent telemetry, and
the first ~20 utterances. Mostly a smoke-test for HistoricalRunHandle
during P8.1 development; the TUI in P8.2+ will subsume this.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wonderland.observer import HistoricalRunHandle


def fmt_cost(c: float) -> str:
    return f"${c:.4f}"


def fmt_duration(s: float | None) -> str:
    if s is None:
        return "—"
    if s < 60:
        return f"{s:.1f}s"
    return f"{s / 60:.1f}m"


def render_summary(handle: HistoricalRunHandle) -> None:
    s = handle.summary()
    print("=" * 78)
    print(f"Run: {s.run_id or '(no run_id)'}")
    print("=" * 78)
    print(f"Workflow:     {s.workflow_name}")
    if s.directive:
        snippet = s.directive[:120] + ("…" if len(s.directive) > 120 else "")
        print(f"Directive:    {snippet}")
    if s.project_root:
        print(f"Project:      {s.project_root}")
    if s.started_at and s.ended_at:
        elapsed = (s.ended_at - s.started_at).total_seconds()
        print(f"Elapsed:      {fmt_duration(elapsed)} ({s.started_at} → {s.ended_at})")
    print(f"Cost:         {fmt_cost(s.total_cost)} · {s.total_calls} LLM calls")
    if s.outcome:
        print(f"Outcome:      {s.outcome}")
    print()


def render_meetings(handle: HistoricalRunHandle) -> None:
    print("─" * 78)
    print("Meetings")
    print("─" * 78)
    print(
        f"  {'label':6s}  {'name':30s}  {'outcome':15s}  {'time':>7s}  "
        f"{'calls':>6s}  {'cost':>9s}"
    )
    for m in handle.meetings():
        name = (m.name or "—")[:30]
        outcome = (m.outcome or "—")[:15]
        time_s = fmt_duration(m.elapsed_seconds)
        print(
            f"  {m.label:6s}  {name:30s}  {outcome:15s}  {time_s:>7s}  "
            f"{m.calls:>6d}  {fmt_cost(m.cost):>9s}"
        )
    print()


def render_agents(handle: HistoricalRunHandle) -> None:
    print("─" * 78)
    print("Per-agent telemetry")
    print("─" * 78)
    for t in handle.per_agent_telemetry():
        print(f"  {t.name:18s}  calls={t.calls:>3d}  cost={fmt_cost(t.cost):>9s}")
    print()


def render_utterances(handle: HistoricalRunHandle, limit: int = 20) -> None:
    print("─" * 78)
    print(f"First {limit} utterances")
    print("─" * 78)
    count = 0
    for u in handle.utterances():
        if count >= limit:
            break
        body_preview = (u.content.body or "(no body)").strip().split("\n", 1)[0]
        if len(body_preview) > 80:
            body_preview = body_preview[:80] + "…"
        print(
            f"  [{u.thread_id:20s}] {u.speaker.name:18s} "
            f"{u.speech_act.value:14s}  {body_preview}"
        )
        count += 1
    if count >= limit:
        total = sum(1 for _ in handle.utterances())
        print(f"  ... and {total - limit} more")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "snapshot_dir",
        type=Path,
        help="Path to a snapshot dir (e.g. analyses/data/029-substrate-convergence/v6/)",
    )
    parser.add_argument(
        "--utterance-limit",
        type=int,
        default=20,
        help="How many utterances to print (default 20).",
    )
    args = parser.parse_args()

    try:
        handle = HistoricalRunHandle(args.snapshot_dir)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    render_summary(handle)
    render_meetings(handle)
    render_agents(handle)
    render_utterances(handle, limit=args.utterance_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
