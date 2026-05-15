#!/usr/bin/env bash
# Wipe design-pass artifacts + episodic memory for a project so the
# next tdd-design run starts from a clean slate. Keeps the discovery
# output (milestones + requirements) and run history.
#
# Usage:
#   scripts/wipe-design.sh <project-name>
#   scripts/wipe-design.sh <project-name> --keep-memory
#   scripts/wipe-design.sh <project-name> --dry-run
#
# Examples:
#   scripts/wipe-design.sh validation4
#   scripts/wipe-design.sh discovery3 --keep-memory
#
# Conventions:
#   - Default wipes episodic memory (every prior pilot showed that
#     stale memory bleeds phantom-slug references into the next run).
#   - --keep-memory preserves .wonderland/memory/ if you want cross-
#     run learning intact.
#   - --dry-run prints what would be removed without touching disk.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    cat >&2 <<EOF
Usage: $0 <project-name> [--keep-memory] [--dry-run]

Wipes design artifacts in projects/<project-name>/.wonderland/:
  stories/  features/  tickets/  architecture/  contract-notes/
  reviews/  rulings/  memory/  feature-states.jsonl  ticket-states.jsonl

Keeps:
  milestones/  requirements/  runs/  telemetry/
  phase-events.jsonl  tool-calls.jsonl  project.yaml
EOF
    exit 2
fi

PROJECT="$1"
shift

KEEP_MEMORY=false
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --keep-memory) KEEP_MEMORY=true ;;
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown arg: $arg" >&2; exit 2 ;;
    esac
done

WONDERLAND_DIR="projects/$PROJECT/.wonderland"

if [[ ! -d "$WONDERLAND_DIR" ]]; then
    echo "No .wonderland directory at $WONDERLAND_DIR" >&2
    exit 1
fi

# Collect paths to wipe.
targets=(
    "$WONDERLAND_DIR/stories"
    "$WONDERLAND_DIR/features"
    "$WONDERLAND_DIR/tickets"
    "$WONDERLAND_DIR/architecture"
    "$WONDERLAND_DIR/contract-notes"
    "$WONDERLAND_DIR/reviews"
    "$WONDERLAND_DIR/rulings"
    "$WONDERLAND_DIR/feature-states.jsonl"
    "$WONDERLAND_DIR/ticket-states.jsonl"
)

if [[ "$KEEP_MEMORY" == false ]]; then
    targets+=("$WONDERLAND_DIR/memory")
fi

# Filter to paths that actually exist so the dry-run output is honest.
existing=()
for t in "${targets[@]}"; do
    if [[ -e "$t" ]]; then
        existing+=("$t")
    fi
done

if [[ ${#existing[@]} -eq 0 ]]; then
    echo "Nothing to wipe in $WONDERLAND_DIR — already clean."
    exit 0
fi

action="Wiping"
[[ "$DRY_RUN" == true ]] && action="[dry-run] Would wipe"
echo "$action in $WONDERLAND_DIR:"
for t in "${existing[@]}"; do
    rel="${t#$WONDERLAND_DIR/}"
    echo "  - $rel"
done

if [[ "$DRY_RUN" == false ]]; then
    rm -rf "${existing[@]}"
    echo "Done."
fi
