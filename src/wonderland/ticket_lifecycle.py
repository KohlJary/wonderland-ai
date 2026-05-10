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


def transition(
    project_root: Path,
    ticket_slug: str,
    to_state: TicketState,
    by: str,
    notes: str | None = None,
) -> TransitionRecord:
    """Append a state-transition record after validating the move.
    Raises ``IllegalTransitionError`` for illegal moves."""
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
    return record


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
    return record


__all__ = [
    "IllegalTransitionError",
    "LEGAL_TRANSITIONS",
    "TICKET_STATES_FILENAME",
    "TicketState",
    "TransitionRecord",
    "all_transitions",
    "back_fill_state",
    "get_state",
    "list_tickets_in_state",
    "transition",
    "transitions_for",
]
