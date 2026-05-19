"""Ticket lifecycle — append-only log of ticket state transitions.

Mirrors ``feature_lifecycle`` shape one level down: each ticket
carries its own state machine so the operator can re-queue
individual tickets when an implementation iteration aborts
(budget cap, error, etc.) without re-running the whole feature.

The minimum-viable substrate this initial cut adds:

  - ``TicketState`` enum (PENDING / QUEUED / IN_PROGRESS / DONE /
    ABORTED) — fewer states than features because tickets are
    leaves on the work tree.
  - Append-only log at ``.wonderland/ticket-states.jsonl`` parallel
    to feature-states.jsonl.
  - ``get_state`` / ``transition`` / ``back_fill_state`` /
    ``list_tickets_in_state`` mirroring the feature_lifecycle API.

Workflow integration (filtering imp runs to operator-queued
tickets) is layered on top and stays backward-compatible: when no
ticket has an explicit ``QUEUED`` state, the existing
"iterate all tickets of queued features" path runs unchanged.
The new filter only activates when at least one ticket is
explicitly queued for the parent feature in question, at which
point the iteration scopes to that set.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


TICKET_STATES_FILENAME = "ticket-states.jsonl"


class TicketState(StrEnum):
    """Lifecycle states a ticket can occupy.

    - ``pending``: ticket exists on disk but hasn't been iterated
      or explicitly queued by the operator. Default for any ticket
      that comes out of M3 decomposition.
    - ``queued``: operator has marked this ticket for the next
      implementation run. The imp workflow filters to queued
      tickets when at least one is set on the parent feature.
    - ``in_progress``: tea-party / implementation / review is
      actively iterating this ticket. Set by the substrate at
      iteration start, cleared at iteration end.
    - ``done``: implementation shipped + review verdict positive.
      Terminal in the happy-path sense.
    - ``aborted``: last iteration tripped a budget cap or error
      and didn't ship an implementation. Operator can re-queue
      to retry.
    """

    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ABORTED = "aborted"


# Legal forward transitions. Fewer states than feature_lifecycle —
# tickets don't have an explicit design phase, just a queue /
# work / outcome cycle. Re-queueing from any non-pending state is
# allowed so the operator can retry aborted tickets and also
# re-queue done ones if they decide more work is needed (the
# substrate doesn't try to be opinionated about "done" being
# strictly final).
LEGAL_TRANSITIONS: dict[TicketState | None, frozenset[TicketState]] = {
    None: frozenset({TicketState.PENDING, TicketState.QUEUED}),
    TicketState.PENDING: frozenset({
        TicketState.QUEUED,
    }),
    TicketState.QUEUED: frozenset({
        TicketState.PENDING,  # un-queue
        TicketState.IN_PROGRESS,
    }),
    TicketState.IN_PROGRESS: frozenset({
        TicketState.DONE,
        TicketState.ABORTED,
        TicketState.QUEUED,  # operator un-aborts a stuck iteration
    }),
    TicketState.DONE: frozenset({
        TicketState.QUEUED,  # operator wants to rework
    }),
    TicketState.ABORTED: frozenset({
        TicketState.QUEUED,  # the canonical retry path
        TicketState.PENDING,  # operator gives up on this ticket
    }),
}


class IllegalTransitionError(ValueError):
    """Raised when ``transition()`` is asked to move a ticket into
    a state its current state doesn't permit."""


class TransitionRecord(BaseModel):
    """One state-transition event in the append-only log."""

    ticket_slug: str = Field(min_length=1)
    from_state: TicketState | None = Field(default=None)
    to_state: TicketState
    by: str = Field(min_length=1)
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = Field(default=None)


def _registry_path(project_root: Path) -> Path:
    return project_root / ".wonderland" / TICKET_STATES_FILENAME


def _append_record(project_root: Path, record: TransitionRecord) -> None:
    """Atomic-ish append. Same idiom as feature_lifecycle — POSIX
    write-line atomicity covers concurrent appends under 4KB."""
    path = _registry_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = record.model_dump_json() + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def all_transitions(project_root: Path) -> list[TransitionRecord]:
    """Every transition logged for this project, in append order.
    Empty list when the log doesn't exist; malformed lines skipped."""
    path = _registry_path(project_root)
    if not path.is_file():
        return []
    records: list[TransitionRecord] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(TransitionRecord.model_validate(data))
            except (json.JSONDecodeError, ValueError):
                continue
    return records


def transitions_for(
    project_root: Path, ticket_slug: str
) -> list[TransitionRecord]:
    """Chronological history for one ticket."""
    return [
        r for r in all_transitions(project_root)
        if r.ticket_slug == ticket_slug
    ]


def get_state(
    project_root: Path, ticket_slug: str
) -> TicketState | None:
    """Current state — the to_state of the most recent transition.
    Returns None when the ticket has no log entries (interpret as
    PENDING-by-default at the caller's discretion)."""
    history = transitions_for(project_root, ticket_slug)
    if not history:
        return None
    return history[-1].to_state


def list_tickets_in_state(
    project_root: Path, state: TicketState
) -> list[str]:
    """Slugs of tickets currently in the given state. Walks the
    full log to compute current-state-per-ticket, then filters."""
    current: dict[str, TicketState] = {}
    for record in all_transitions(project_root):
        current[record.ticket_slug] = record.to_state
    matches = [slug for slug, s in current.items() if s == state]
    matches.sort()
    return matches


# Substrate bug 85aaee91 fix: lifecycle ↔ md-status mapping.
# The lifecycle TicketState (pending / queued / in_progress / done /
# aborted) and the md-file TicketStatus (open / in_flight / blocked /
# done / dropped) are two different vocabularies for the same
# concept. Pre-fix, the md status field was set at write time and
# never updated, so the .md said ``open`` even after the lifecycle
# transitioned the ticket through done. Operators using
# ``grep Status: tickets/*.md`` saw stale state; the dashboard's
# audit view (which reads the ledger) saw correct state; the two
# diverged silently.
_LIFECYCLE_TO_MD_STATUS: dict[TicketState, str] = {
    TicketState.PENDING: "open",
    TicketState.QUEUED: "open",
    TicketState.IN_PROGRESS: "in_flight",
    TicketState.DONE: "done",
    TicketState.ABORTED: "dropped",
}


def _propagate_state_to_md(
    project_root: Path, ticket_slug: str, to_state: TicketState,
) -> None:
    """Update the ticket .md file's ``**Status:**`` field to mirror
    the lifecycle state. Best-effort: silently skips when the
    ticket file can't be found or rewritten — the ledger remains
    canonical, this is just keeping the md cosmetic field honest.

    Substrate bug ``85aaee91`` history: pipeline_runner uses the
    ledger correctly (via ``get_state``), but operators inspecting
    tickets directly (``cat tickets/x.md``) saw stale ``Status:``
    fields. The deeper class of bug was multi-source-of-truth
    drift — different surfaces consulting different sources. This
    hook makes the ledger the single point of truth that
    cascades into the md, eliminating the drift class for
    ticket-level state.
    """
    import re
    from wonderland.ticket import TicketRegistry

    try:
        record = TicketRegistry(project_root).find_by_slug(ticket_slug)
    except Exception:  # noqa: BLE001
        return
    if record is None:
        return
    try:
        text = record.path.read_text(encoding="utf-8")
    except OSError:
        return
    md_status = _LIFECYCLE_TO_MD_STATUS.get(to_state, "open")
    new_text, replaced = re.subn(
        r"^(\*\*Status:\*\*)\s*\S+",
        rf"\1 {md_status}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if replaced == 0 or new_text == text:
        return
    try:
        record.path.write_text(new_text, encoding="utf-8")
    except OSError:
        return


def transition(
    project_root: Path,
    ticket_slug: str,
    to_state: TicketState,
    by: str,
    notes: str | None = None,
) -> TransitionRecord:
    """Append a state-transition record after validating the move.
    Raises ``IllegalTransitionError`` for illegal moves.

    Side effect: the ticket .md file's ``**Status:**`` field is
    re-rendered to mirror the new state (substrate bug
    ``85aaee91`` fix — ledger as canonical source of truth,
    md as cosmetic mirror). Best-effort; ledger write is the
    primary contract.
    """
    current = get_state(project_root, ticket_slug)
    legal = LEGAL_TRANSITIONS.get(current, frozenset())
    if to_state not in legal:
        from_label = current.value if current else "(initial)"
        legal_labels = sorted(s.value for s in legal) or [
            "(none — terminal state)"
        ]
        raise IllegalTransitionError(
            f"Illegal transition for ticket {ticket_slug!r}: "
            f"{from_label} → {to_state.value}. "
            f"Legal moves from {from_label}: {legal_labels}"
        )
    record = TransitionRecord(
        ticket_slug=ticket_slug,
        from_state=current,
        to_state=to_state,
        by=by,
        notes=notes,
    )
    _append_record(project_root, record)
    _propagate_state_to_md(project_root, ticket_slug, to_state)
    return record


# Hardcoded legal paths between ticket states — the state machine
# is small enough that explicit paths beat runtime BFS. Each entry
# names the intermediate states to traverse (not including the
# starting state). ``chain_transition`` walks the path step by step
# through ``transition`` so the LEGAL_TRANSITIONS gate enforces
# each individual move. Used by dashboard bulk operations (queue
# all / mark ready / re-design) where the operator's intent is a
# target state regardless of where the ticket starts.
_LEGAL_PATHS: dict[
    tuple["TicketState | None", "TicketState"], list["TicketState"]
] = {
    # From None (no record): back-fill happens separately in
    # ``chain_transition``; entries here cover the post-back-fill
    # PENDING starting point.
    (None, TicketState.PENDING): [],
    (None, TicketState.QUEUED): [TicketState.QUEUED],
    (None, TicketState.IN_PROGRESS): [
        TicketState.QUEUED, TicketState.IN_PROGRESS
    ],
    (None, TicketState.DONE): [
        TicketState.QUEUED,
        TicketState.IN_PROGRESS,
        TicketState.DONE,
    ],
    # From PENDING.
    (TicketState.PENDING, TicketState.QUEUED): [TicketState.QUEUED],
    (TicketState.PENDING, TicketState.IN_PROGRESS): [
        TicketState.QUEUED, TicketState.IN_PROGRESS
    ],
    (TicketState.PENDING, TicketState.DONE): [
        TicketState.QUEUED,
        TicketState.IN_PROGRESS,
        TicketState.DONE,
    ],
    # From QUEUED.
    (TicketState.QUEUED, TicketState.PENDING): [TicketState.PENDING],
    (TicketState.QUEUED, TicketState.IN_PROGRESS): [
        TicketState.IN_PROGRESS
    ],
    (TicketState.QUEUED, TicketState.DONE): [
        TicketState.IN_PROGRESS, TicketState.DONE
    ],
    # From IN_PROGRESS.
    (TicketState.IN_PROGRESS, TicketState.QUEUED): [
        TicketState.QUEUED
    ],
    (TicketState.IN_PROGRESS, TicketState.PENDING): [
        TicketState.QUEUED, TicketState.PENDING
    ],
    (TicketState.IN_PROGRESS, TicketState.DONE): [TicketState.DONE],
    (TicketState.IN_PROGRESS, TicketState.ABORTED): [
        TicketState.ABORTED
    ],
    # From DONE.
    (TicketState.DONE, TicketState.QUEUED): [TicketState.QUEUED],
    (TicketState.DONE, TicketState.PENDING): [
        TicketState.QUEUED, TicketState.PENDING
    ],
    # From ABORTED.
    (TicketState.ABORTED, TicketState.PENDING): [TicketState.PENDING],
    (TicketState.ABORTED, TicketState.QUEUED): [TicketState.QUEUED],
}


def chain_transition(
    project_root: Path,
    ticket_slug: str,
    target: TicketState,
    *,
    by: str,
    notes: str | None = None,
) -> TicketState:
    """Multi-step legal transition from the ticket's current state
    to ``target``. Walks intermediate states via individual
    ``transition`` calls so each step is gated by
    ``LEGAL_TRANSITIONS`` and shows up in the audit log.

    No-record tickets are back-filled to PENDING first (the
    standard initial state). Tickets already at ``target`` no-op.
    Raises ``IllegalTransitionError`` only when no path exists
    from current to target in ``_LEGAL_PATHS``.

    Returns the final state (= target on success).
    """
    current = get_state(project_root, ticket_slug)
    if current is None:
        back_fill_state(
            project_root,
            ticket_slug,
            TicketState.PENDING,
            notes=notes
            or "Back-filled before chain transition from dashboard",
        )
        current = TicketState.PENDING
    if current == target:
        return current
    path = _LEGAL_PATHS.get((current, target))
    if path is None:
        raise IllegalTransitionError(
            f"chain_transition for {ticket_slug!r}: no legal path "
            f"from {current.value} to {target.value}"
        )
    for step in path:
        transition(
            project_root,
            ticket_slug,
            step,
            by=by,
            notes=notes,
        )
    return target


def back_fill_state(
    project_root: Path,
    ticket_slug: str,
    state: TicketState,
    *,
    notes: str | None = None,
) -> TransitionRecord:
    """Migration helper for tickets that exist on disk but have no
    transition log. Refuses to back-fill tickets that already have
    a recorded state."""
    if get_state(project_root, ticket_slug) is not None:
        raise ValueError(
            f"ticket {ticket_slug!r} already has a recorded state; "
            f"back_fill_state is for migration only"
        )
    record = TransitionRecord(
        ticket_slug=ticket_slug,
        from_state=None,
        to_state=state,
        by="system_backfill",
        notes=notes or "Back-filled from pre-lifecycle ticket registry",
    )
    _append_record(project_root, record)
    _propagate_state_to_md(project_root, ticket_slug, state)
    return record


__all__ = [
    "IllegalTransitionError",
    "LEGAL_TRANSITIONS",
    "TICKET_STATES_FILENAME",
    "TicketState",
    "TransitionRecord",
    "all_transitions",
    "back_fill_state",
    "chain_transition",
    "get_state",
    "list_tickets_in_state",
    "transition",
    "transitions_for",
]
