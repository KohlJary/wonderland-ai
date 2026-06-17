"""Measure the implement-phase artifact-reliability gap from telemetry.

Reconstructs each Tweedle (tweedledee/tweedledum) deliberation in the
`implement` phase by pairing its `PriorityWindowOpenEvent` with the
following `AgentActEvent`/`AgentPassEvent` in `.wonderland/phase-events.jsonl`,
then joins `.wonderland/tool-calls.jsonl` (by timestamp) to see what the
deliberation actually DID inside that window:

  - edits  = write_file / str_replace / create_file / edit_file calls
  - iters  = distinct LLM round-trips (parallel tool calls in one response
             collapse to one; a >1s gap starts a new iteration)
  - outcome = ACT (emitted an utterance/artifact) vs PASS (silence)

The failure class we're tracking: a deliberation that made edits but ended
in PASS — work landed on disk, no implementation artifact emitted. Most of
these carry the >=ITER_EXHAUST exhaustion signature (read/edit until the
tool-loop cap, then silence).

WHY str_replace matters: Tweedles edit via str_replace ~10x more than
write_file (obol: 302 vs 34). A measurement — or a substrate write-tracker
like `_last_write_file_paths` — that only counts write_file is blind to ~90%
of edits. Always count the full edit set.

This is the baseline to diff against post-split-budget runs: the
edited-but-passed count (esp. the >=17-iter share) should drop once reads
stop starving the write budget.

Usage:
    uv run python scripts/implement_artifact_gap.py projects/obol-260522-1
    uv run python scripts/implement_artifact_gap.py projects/obol-260522-1 projects/mvp-demo-redux
    uv run python scripts/implement_artifact_gap.py --all
    uv run python scripts/implement_artifact_gap.py projects/obol-260522-1 --exhaust-iters 17
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

TWEEDLES = {"tweedledee", "tweedledum"}
EDIT_TOOLS = {"write_file", "str_replace", "create_file", "edit_file"}
IMPLEMENT_PHASE = "implement"
ITER_GAP_S = 1.0  # >1s between an agent's tool calls => new LLM iteration


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _iters(times: list[datetime]) -> int:
    """Collapse a sorted timestamp list into LLM-iteration count."""
    if not times:
        return 0
    n = 1
    for prev, cur in zip(times, times[1:]):
        if (cur - prev).total_seconds() > ITER_GAP_S:
            n += 1
    return n


def analyze(project: Path, exhaust_iters: int) -> dict:
    wonder = project / ".wonderland"
    events = _load_jsonl(wonder / "phase-events.jsonl")
    calls = _load_jsonl(wonder / "tool-calls.jsonl")
    events.sort(key=lambda e: e["timestamp"])

    # Per-tweedle timelines: all calls (for iteration counting) + edits only.
    all_calls = {a: [] for a in TWEEDLES}
    edit_calls = {a: [] for a in TWEEDLES}
    for c in calls:
        a = c.get("agent_id")
        if a in TWEEDLES:
            t = _parse(c["timestamp"])
            all_calls[a].append(t)
            if c["tool_name"] in EDIT_TOOLS:
                edit_calls[a].append(t)

    # Pair implement-phase window-open -> act/pass per tweedle.
    spans = []  # (agent, start, end, passed)
    open_at: dict[str, datetime] = {}
    for e in events:
        a = e.get("agent_id")
        if a not in TWEEDLES:
            continue
        k = e["_kind"]
        if k == "PriorityWindowOpenEvent" and e.get("phase_name") == IMPLEMENT_PHASE:
            open_at[a] = _parse(e["timestamp"])
        elif k in ("AgentActEvent", "AgentPassEvent") and a in open_at:
            spans.append((a, open_at.pop(a), _parse(e["timestamp"]), k == "AgentPassEvent"))

    def within(lst, a, b):
        return [t for t in lst if a <= t <= b]

    r = dict(
        delibs=0, act=0, passed=0, act_edited=0,
        pass_edited=0, pass_edited_exhausted=0,
        pass_noedit_exhausted=0, pass_noedit_legit=0,
    )
    for agent, s, e, passed in spans:
        r["delibs"] += 1
        edits = within(edit_calls[agent], s, e)
        it = _iters(within(all_calls[agent], s, e))
        if not passed:
            r["act"] += 1
            if edits:
                r["act_edited"] += 1
        else:
            r["passed"] += 1
            if edits:
                r["pass_edited"] += 1
                if it >= exhaust_iters:
                    r["pass_edited_exhausted"] += 1
            elif it >= exhaust_iters:
                r["pass_noedit_exhausted"] += 1
            else:
                r["pass_noedit_legit"] += 1

    impl_records = len(list((wonder / "implementations").glob("*.md"))) if (wonder / "implementations").exists() else 0
    tickets = len(list((wonder / "tickets").glob("*"))) if (wonder / "tickets").exists() else 0
    r["impl_records"] = impl_records
    r["tickets"] = tickets
    return r


def _print(name: str, r: dict, exhaust_iters: int) -> None:
    d = r["delibs"]
    if d == 0:
        print(f"\n{name}: no implement-phase Tweedle deliberations (different workflow?)")
        return
    pe = r["pass_edited"]
    pct = 100 * pe // d if d else 0
    print(f"\n{name}: {d} implement delibs  (ACT={r['act']}, PASS={r['passed']})")
    print(f"   ACT with edits          = {r['act_edited']}/{r['act']}")
    print(f"   EDITED but PASSED (no artifact this rotation) = {pe}  ({pct}% of delibs)")
    print(f"     ...of which >={exhaust_iters}-iter (exhaustion signature)  = {r['pass_edited_exhausted']}")
    print(f"   PASS no edits, >={exhaust_iters}it (read->exhaust->never built) = {r['pass_noedit_exhausted']}")
    print(f"   PASS no edits, <{exhaust_iters}it  (legit: no work this rotation) = {r['pass_noedit_legit']}")
    print(f"   [ticket-level gross] impl_records={r['impl_records']}  tickets={r['tickets']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projects", nargs="*", help="project dirs (e.g. projects/obol-260522-1)")
    ap.add_argument("--all", action="store_true", help="scan every projects/* with a tool-calls.jsonl")
    ap.add_argument("--exhaust-iters", type=int, default=17,
                    help="iteration count treated as the exhaustion signature (default 17; tool cap was 20 pre-split)")
    args = ap.parse_args()

    if args.all:
        roots = sorted(p.parent.parent for p in Path("projects").glob("*/.wonderland/tool-calls.jsonl"))
    else:
        roots = [Path(p) for p in args.projects]
    if not roots:
        ap.error("pass project dirs or --all")

    for proj in roots:
        try:
            r = analyze(proj, args.exhaust_iters)
        except FileNotFoundError:
            print(f"\n{proj.name}: missing telemetry")
            continue
        _print(proj.name, r, args.exhaust_iters)


if __name__ == "__main__":
    main()
