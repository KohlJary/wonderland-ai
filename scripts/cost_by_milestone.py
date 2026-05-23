"""Per-milestone / per-feature cost rollup from telemetry per_thread_cost keys.

Walks a project's `.wonderland/telemetry/run-*.json` files, parses every
run's `per_thread_cost` dict (keyed by `<phase>-<feature_slug>` for per-
feature meetings, or just `<phase>` for project-level phases like
scoping/composition/milestone-plan), looks up each feature_slug's parent
milestone in `.wonderland/features/`, and produces a per-milestone rollup
that's robust to mixed-feature implement runs (e.g. an implement run
that processes both M0 and M2 features in the same wonderland invocation
because a stuck `in_progress` ticket pulled cross-milestone work).

Usage:
    uv run python scripts/cost_by_milestone.py projects/obol-260522
    uv run python scripts/cost_by_milestone.py projects/obol-260522 --workflow tdd-implement
    uv run python scripts/cost_by_milestone.py projects/obol-260522 --by-feature

Why this exists: cost-per-milestone analysis breaks down when a single
wonderland run is impure (multi-milestone work in one process). Run-
level totals from status.json conflate. Telemetry's per_thread_cost is
the only granular attribution available, so this script re-aggregates
from that primitive.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# Telemetry per_thread_cost keys come in three shapes:
#   1. <phase>                                — project-level phases with no
#                                                feature anchor (scoping,
#                                                composition, planning)
#   2. <phase>-<feature_slug>                 — design-phase per-feature
#                                                meetings (decomposition,
#                                                consolidation, architecture,
#                                                contract-negotiation)
#   3. pipe.<feature_slug>.<phase>[-<ticket>] — implement workflow pipelined
#                                                meetings (tea-party,
#                                                implementation, validate,
#                                                review, verify)
KNOWN_PHASES = {
    "scoping", "composition", "decomposition", "consolidation",
    "architecture", "contract-negotiation", "tea-party", "implement",
    "implementation", "validate", "review", "verify", "milestone-plan",
    "foundation-scoping", "discovery", "planning",
}


def split_meeting_id(meeting_id: str) -> tuple[str, str | None]:
    """Split `meeting_id` into `(phase, feature_slug_or_none)`.

    Examples:
      "scoping" -> ("scoping", None)
      "planning" -> ("planning", None)
      "decomposition-my-feature-slug" -> ("decomposition", "my-feature-slug")
      "contract-negotiation-csv-ingestion" -> ("contract-negotiation",
                                              "csv-ingestion")
      "pipe.data-schema.tea-party-some-ticket" -> ("tea-party", "data-schema")
      "pipe.data-schema.review-data-schema" -> ("review", "data-schema")
    """
    # Shape 3: pipelined implement keys
    if meeting_id.startswith("pipe."):
        rest = meeting_id[len("pipe."):]
        try:
            feature_slug, tail = rest.split(".", 1)
        except ValueError:
            return meeting_id, None
        # tail is <phase>[-<ticket>]; find the longest known-phase prefix
        for phase in sorted(KNOWN_PHASES, key=len, reverse=True):
            if tail == phase or tail.startswith(phase + "-"):
                return phase, feature_slug
        return tail, feature_slug

    # Shapes 1+2: try matching the longest known phase prefix first
    for phase in sorted(KNOWN_PHASES, key=len, reverse=True):
        if meeting_id == phase:
            return phase, None
        if meeting_id.startswith(phase + "-"):
            return phase, meeting_id[len(phase) + 1:]
    return meeting_id, None


def load_feature_milestones(features_dir: Path) -> dict[str, str]:
    """Map feature_slug -> milestone_slug from feature files' `**Milestone:**`.

    The feature file's Milestone line is shaped:
        **Milestone:** <guid>:<milestone-slug>
    We return just the milestone-slug part (e.g. "m0-data-layer-...").
    Feature filename convention is feature-<guid_short>-<slug>.md.
    """
    out: dict[str, str] = {}
    if not features_dir.exists():
        return out
    fname_re = re.compile(r"^feature-[A-Z0-9]+-(.+)\.md$")
    # The Milestone line takes two shapes on disk:
    #   **Milestone:** <guid>:<slug>
    #   **Milestone:** <slug>             (no guid prefix, post T-ab32 era)
    # `[^:\n]+` is bounded so the optional `<guid>:` group can't greedy-eat
    # through to the NEXT line's colon (e.g. `**Sources:**`), which would
    # otherwise capture the literal `**` from that line as the milestone.
    milestone_re = re.compile(r"^\*\*Milestone:\*\*\s+(?:[^:\n]+:)?(\S+)", re.M)
    for fp in features_dir.iterdir():
        m = fname_re.match(fp.name)
        if not m:
            continue
        slug = m.group(1)
        body = fp.read_text(encoding="utf-8")
        mm = milestone_re.search(body)
        if mm:
            out[slug] = mm.group(1)
    return out


def main() -> None:
    doc = __doc__ or ""
    ap = argparse.ArgumentParser(description=doc.splitlines()[0] if doc else "")
    ap.add_argument("project_root", type=Path,
                    help="path to a project dir containing .wonderland/")
    ap.add_argument("--workflow", default=None,
                    help="restrict to one workflow (tdd-design, tdd-implement, ...)")
    ap.add_argument("--by-feature", action="store_true",
                    help="show per-feature breakdown within each milestone")
    ap.add_argument("--by-run", action="store_true",
                    help="show per-run contributions to each milestone")
    args = ap.parse_args()

    wl = args.project_root / ".wonderland"
    if not wl.exists():
        raise SystemExit(f"no .wonderland dir at {args.project_root}")

    feature_milestones = load_feature_milestones(wl / "features")
    if not feature_milestones:
        print(f"warning: no features found under {wl / 'features'}")

    # milestone -> {cost, meetings, runs, features: set, by_feature: {slug -> cost}}
    per_milestone: dict[str, dict] = defaultdict(
        lambda: {"cost": 0.0, "meetings": 0, "runs": set(),
                 "by_feature": defaultdict(float), "by_run": defaultdict(float)})
    # cost on phases with no per-feature attribution (scoping, composition, etc.)
    overhead_per_workflow: dict[str, float] = defaultdict(float)
    # cost on feature meetings whose feature doesn't have a known milestone
    orphan_cost = 0.0
    orphan_features: set[str] = set()

    runs_dir = wl / "runs"
    telemetry_dir = wl / "telemetry"

    for tel_fp in sorted(telemetry_dir.glob("run-*.json")):
        rid = tel_fp.stem[len("run-"):]
        tel = json.loads(tel_fp.read_text(encoding="utf-8"))

        # workflow lookup from status.json
        status_fp = runs_dir / rid / "status.json"
        if not status_fp.exists():
            continue
        status = json.loads(status_fp.read_text(encoding="utf-8"))
        wf = status.get("workflow", "?")
        if args.workflow and wf != args.workflow:
            continue

        for thread_id, cost in tel.get("per_thread_cost", {}).items():
            _, feature_slug = split_meeting_id(thread_id)
            if feature_slug is None:
                overhead_per_workflow[wf] += cost
                continue
            milestone = feature_milestones.get(feature_slug)
            if milestone is None:
                orphan_cost += cost
                orphan_features.add(feature_slug)
                continue
            bucket = per_milestone[milestone]
            bucket["cost"] += cost
            bucket["meetings"] += 1
            bucket["runs"].add(rid)
            bucket["by_feature"][feature_slug] += cost
            bucket["by_run"][rid] += cost

    title_wf = args.workflow if args.workflow else "all workflows"
    print(f"=== Per-milestone cost rollup ({title_wf}) ===")
    print(f"     project: {args.project_root}")
    print()

    total = 0.0
    for ms in sorted(per_milestone.keys()):
        b = per_milestone[ms]
        total += b["cost"]
        print(f"  {ms}")
        print(f"    cost:     ${b['cost']:.4f}")
        print(f"    meetings: {b['meetings']}")
        print(f"    runs:     {len(b['runs'])}")
        print(f"    features: {len(b['by_feature'])}")
        if args.by_feature:
            for slug, cost in sorted(b["by_feature"].items(),
                                     key=lambda kv: -kv[1]):
                print(f"      {cost:8.4f}  {slug}")
        if args.by_run:
            for rid, cost in sorted(b["by_run"].items()):
                print(f"      run {rid}  ${cost:.4f}")
        print()

    print(f"  Per-milestone subtotal:   ${total:.4f}")
    if overhead_per_workflow:
        print(f"  Project-phase overhead (scoping/composition/milestone-plan):")
        for wf, c in sorted(overhead_per_workflow.items()):
            print(f"    {wf:18}  ${c:.4f}")
    if orphan_cost > 0:
        print(f"  Orphan cost (feature not in features/ dir): ${orphan_cost:.4f}")
        print(f"    orphan features: {sorted(orphan_features)}")
    grand_total = total + sum(overhead_per_workflow.values()) + orphan_cost
    print(f"  GRAND TOTAL ({title_wf}):       ${grand_total:.4f}")


if __name__ == "__main__":
    main()
