"""Tests for ``wonderland.ticket_lifecycle`` — the parallel-to-
feature_lifecycle state machine for tickets. Operator queues
specific tickets for re-run when an iteration aborts (budget cap,
error) so they don't have to re-run the whole feature."""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.ticket_lifecycle import (
    IllegalTransitionError,
    TicketState,
    back_fill_state,
    get_state,
    list_tickets_in_state,
    transition,
    transitions_for,
)


def test_get_state_returns_none_for_unrecorded_ticket(
    tmp_path: Path,
) -> None:
    assert get_state(tmp_path, "ticket-foo") is None


def test_pending_to_queued_then_in_progress(tmp_path: Path) -> None:
    """The canonical operator-initiated queue path."""
    transition(tmp_path, "ticket-a", TicketState.PENDING, by="system")
    assert get_state(tmp_path, "ticket-a") == TicketState.PENDING

    transition(tmp_path, "ticket-a", TicketState.QUEUED, by="operator")
    assert get_state(tmp_path, "ticket-a") == TicketState.QUEUED

    transition(
        tmp_path, "ticket-a", TicketState.IN_PROGRESS, by="system"
    )
    assert get_state(tmp_path, "ticket-a") == TicketState.IN_PROGRESS


def test_in_progress_to_aborted_then_requeue(tmp_path: Path) -> None:
    """The retry-after-budget-abort path: in_progress → aborted →
    queued. This is exactly the operator's case after a tea-party /
    implementation iteration trips its budget cap."""
    transition(tmp_path, "ticket-a", TicketState.QUEUED, by="operator")
    transition(
        tmp_path, "ticket-a", TicketState.IN_PROGRESS, by="system"
    )
    transition(
        tmp_path,
        "ticket-a",
        TicketState.ABORTED,
        by="system",
        notes="meeting budget exceeded",
    )
    assert get_state(tmp_path, "ticket-a") == TicketState.ABORTED

    # Re-queue for retry.
    transition(
        tmp_path, "ticket-a", TicketState.QUEUED, by="operator",
        notes="retry after budget abort",
    )
    assert get_state(tmp_path, "ticket-a") == TicketState.QUEUED


def test_illegal_transition_raises(tmp_path: Path) -> None:
    """Pending → done isn't legal; ticket must go through
    queued + in_progress first."""
    transition(tmp_path, "ticket-a", TicketState.PENDING, by="system")
    with pytest.raises(IllegalTransitionError, match="pending"):
        transition(
            tmp_path, "ticket-a", TicketState.DONE, by="operator"
        )


def test_un_queue_path(tmp_path: Path) -> None:
    """Queued → pending lets the operator un-queue a ticket they
    queued by mistake."""
    transition(tmp_path, "ticket-a", TicketState.QUEUED, by="operator")
    transition(tmp_path, "ticket-a", TicketState.PENDING, by="operator")
    assert get_state(tmp_path, "ticket-a") == TicketState.PENDING


def test_list_tickets_in_state(tmp_path: Path) -> None:
    transition(tmp_path, "ticket-a", TicketState.QUEUED, by="operator")
    transition(tmp_path, "ticket-b", TicketState.QUEUED, by="operator")
    transition(tmp_path, "ticket-c", TicketState.PENDING, by="system")
    # ticket-b later un-queued
    transition(tmp_path, "ticket-b", TicketState.PENDING, by="operator")

    queued = list_tickets_in_state(tmp_path, TicketState.QUEUED)
    assert queued == ["ticket-a"]


def test_back_fill_state(tmp_path: Path) -> None:
    """Migration: pre-lifecycle tickets on disk can be back-filled
    to a sensible state. Refuses to back-fill once a state is
    recorded."""
    back_fill_state(
        tmp_path,
        "ticket-old",
        TicketState.PENDING,
        notes="discovered on disk during migration",
    )
    assert get_state(tmp_path, "ticket-old") == TicketState.PENDING

    with pytest.raises(ValueError, match="already has a recorded state"):
        back_fill_state(tmp_path, "ticket-old", TicketState.QUEUED)


def test_transitions_for_returns_chronological_history(
    tmp_path: Path,
) -> None:
    transition(tmp_path, "ticket-a", TicketState.PENDING, by="system")
    transition(tmp_path, "ticket-a", TicketState.QUEUED, by="operator")
    transition(tmp_path, "ticket-other", TicketState.QUEUED, by="operator")
    transition(
        tmp_path, "ticket-a", TicketState.IN_PROGRESS, by="system"
    )

    history = transitions_for(tmp_path, "ticket-a")
    states = [r.to_state for r in history]
    assert states == [
        TicketState.PENDING,
        TicketState.QUEUED,
        TicketState.IN_PROGRESS,
    ]
