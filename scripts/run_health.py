"""One-shot health check for an in-flight (or finished) implement run.

Bundles every validation this session's fixes care about so "check in on
the run" is a single command instead of five ad-hoc queries. Safe to run
mid-run — reads append-only telemetry, never mutates.

    uv run python scripts/run_health.py projects/ldr-ophanic

Sections:
  1. IMPLEMENT  — Tweedle edited-but-passed / exhaustion (split-budget signal;
                  reuses implement_artifact_gap.analyze). Lower = better.
  2. CATERPILLAR— M8 review acts vs passes, and the >=17-iter exhaustion
                  signature (did review actually happen, or silence?).
  3. FRONTEND   — is the M2 TimeCard built AND wired into the app (hollow-build
                  resolution check), or still absent?
  4. PHANTOMS   — non-terminal ledger states with no artifact (should be 0 now
                  that prune tombstones; any new ones = regression).
  5. TICKETS    — current state of the re-queued M2 frontend tickets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from implement_artifact_gap import analyze as analyze_implement  # noqa: E402

TWEEDLES = {"tweedledee", "tweedledum"}
READ = {"read_file", "list_files", "grep", "git_status", "git_diff"}
ITER_GAP = 1.0
M2_FRONTEND_TICKETS = [
    "frontend-time-card-component-with-live-ticking-clock",
    "render-partner-s-local-time-in-their-timezone-updating-client-side-every-second",
    "set-up-react-spa-scaffold-and-dashboard-layout-with-three-card-placeholders",
]


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _latest_run_since(proj: Path):
    """Start time of the most recent run, parsed from the timestamped
    run dir name (e.g. ``20260617T230606``, UTC). Returns a tz-aware
    datetime, or None if no run dirs. Used to scope append-only
    telemetry to the current run."""
    from datetime import timezone
    runs_dir = proj / ".wonderland" / "runs"
    if not runs_dir.is_dir():
        return None
    stamps = []
    for d in runs_dir.iterdir():
        if d.is_dir() and re.fullmatch(r"\d{8}T\d{6}", d.name):
            try:
                stamps.append(datetime.strptime(d.name, "%Y%m%dT%H%M%S")
                              .replace(tzinfo=timezone.utc))
            except ValueError:
                pass
    return max(stamps) if stamps else None


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def _iters(times: list[datetime]) -> int:
    if not times:
        return 0
    n = 1
    for a, b in zip(times, times[1:]):
        if (b - a).total_seconds() > ITER_GAP:
            n += 1
    return n


def section_implement(proj: Path, since=None) -> None:
    print("── 1. IMPLEMENT (split-budget signal) " + "─" * 24)
    try:
        r = analyze_implement(proj, 17, since)
    except Exception as e:  # noqa: BLE001
        print(f"   (no implement data yet: {e})")
        return
    d = r["delibs"]
    if not d:
        print("   no implement-phase deliberations yet")
        return
    print(f"   implement delibs={d}  ACT={r['act']}  PASS={r['passed']}")
    print(f"   edited-but-PASSED (no artifact) = {r['pass_edited']}  "
          f"(>=17it exhaustion = {r['pass_edited_exhausted']})   << want low")
    print(f"   read->exhaust->never-built      = {r['pass_noedit_exhausted']}")


def section_caterpillar(proj: Path, since=None) -> None:
    print("── 2. CATERPILLAR (M8 review vs silence) " + "─" * 20)
    events = sorted(_load(proj / ".wonderland" / "phase-events.jsonl"),
                    key=lambda e: e["timestamp"])
    calls = _load(proj / ".wonderland" / "tool-calls.jsonl")
    cat = sorted(_parse(c["timestamp"]) for c in calls if c["agent_id"] == "caterpillar")
    spans = []
    open_t = None
    for e in events:
        if e.get("agent_id") != "caterpillar":
            continue
        k = e["_kind"]
        if k == "PriorityWindowOpenEvent" and e.get("phase_name") == "review":
            open_t = _parse(e["timestamp"])
        elif k in ("AgentActEvent", "AgentPassEvent") and open_t:
            if since is None or open_t >= since:
                spans.append((open_t, _parse(e["timestamp"]), k == "AgentPassEvent"))
            open_t = None
    if not spans:
        print("   no M8 review deliberations yet")
        return
    acts = sum(1 for *_, p in spans if not p)
    passes = [(a, b) for a, b, p in spans if p]
    exh = sum(1 for a, b in passes
              if _iters([t for t in cat if a <= t <= b]) >= 17)
    print(f"   review deliberations={len(spans)}  ACT(real review)={acts}  PASS(silence)={len(passes)}")
    print(f"   exhaustion-silences (>=17it pass) = {exh}   << want 0")


def section_frontend(proj: Path) -> None:
    print("── 3. FRONTEND (hollow-build resolution) " + "─" * 20)
    tsx = list(proj.glob("src/**/*.tsx")) + list(proj.glob("src/**/*.jsx"))
    tsx = [p for p in tsx if "node_modules" not in str(p)]
    src = "\n".join(p.read_text(errors="ignore") for p in tsx)
    defined = bool(re.search(r"(function|const|class)\s+TimeCard", src))
    imported = bool(re.search(r"import\s+.*TimeCard|<TimeCard", src))
    print(f"   TimeCard defined in source = {defined}")
    print(f"   TimeCard imported/rendered = {imported}   << both True = built+wired")
    if not defined and not imported:
        print("   STILL HOLLOW — TimeCard absent from the code")


def section_phantoms(proj: Path) -> None:
    print("── 4. PHANTOMS (state without artifact) " + "─" * 21)
    try:
        from wonderland.ticket import TicketRegistry
        from wonderland.ticket_lifecycle import (
            TicketState, all_transitions, get_state,
        )
    except Exception as e:  # noqa: BLE001
        print(f"   (lib import failed: {e})")
        return
    reg = TicketRegistry(proj)
    live = {TicketState.PENDING, TicketState.QUEUED, TicketState.IN_PROGRESS}
    slugs = {r.ticket_slug for r in all_transitions(proj)}
    phantoms = [s for s in sorted(slugs)
                if get_state(proj, s) in live and reg.find_by_slug(s) is None]
    if not phantoms:
        print("   0 phantoms   << clean")
    else:
        print(f"   {len(phantoms)} PHANTOM(S) — non-terminal ledger state, no artifact:")
        for s in phantoms:
            st = get_state(proj, s)
            print(f"      {st.value if st else '?':11} {s}")
        print("   (run tombstone_orphaned_ticket_states to heal)")


def section_tickets(proj: Path) -> None:
    print("── 5. M2 FRONTEND TICKETS (re-queued) " + "─" * 23)
    try:
        from wonderland.ticket_lifecycle import get_state
    except Exception as e:  # noqa: BLE001
        print(f"   (lib import failed: {e})")
        return
    for s in M2_FRONTEND_TICKETS:
        st = get_state(proj, s)
        print(f"   {st.value if st else '(none)':12} {s[:58]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project dir, e.g. projects/ldr-ophanic")
    ap.add_argument("--all-runs", action="store_true",
                    help="don't scope to the latest run (count cumulative telemetry)")
    args = ap.parse_args()
    proj = Path(args.project)
    since = None if args.all_runs else _latest_run_since(proj)
    print(f"\n===== run health: {proj.name} =====")
    if since is not None:
        print(f"   scoped to current run (since {since:%Y-%m-%d %H:%M:%S} UTC) "
              f"— pass --all-runs for cumulative\n")
    else:
        print("   cumulative across all runs\n")
    def run(fn, *a):
        try:
            fn(*a)
        except Exception as e:  # noqa: BLE001
            print(f"   (section error: {e})")
        print()

    # Sections 1-2 read append-only telemetry → scoped to the run window.
    # Sections 3-5 are point-in-time (current disk / ledger state).
    run(section_implement, proj, since)
    run(section_caterpillar, proj, since)
    run(section_frontend, proj)
    run(section_phantoms, proj)
    run(section_tickets, proj)


if __name__ == "__main__":
    main()
