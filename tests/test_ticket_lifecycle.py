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
    tombstone,
    tombstone_orphaned_ticket_states,
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


def test_chain_transition_walks_multistep_paths(tmp_path: Path) -> None:
    """``chain_transition`` traverses intermediate states to reach
    any legal target — used by the dashboard's bulk ops.

    Covers:
      - DONE → PENDING (DONE → QUEUED → PENDING)
      - ABORTED → PENDING (single-step)
      - No-record → QUEUED (back-fill PENDING + transition)
      - Idempotent: already at target → no-op
    """
    from wonderland.ticket_lifecycle import (
        TicketState,
        chain_transition,
        get_state,
        transition,
        transitions_for,
    )

    # DONE → PENDING via intermediate QUEUED
    transition(tmp_path, "alpha", TicketState.QUEUED, by="op")
    transition(tmp_path, "alpha", TicketState.IN_PROGRESS, by="sys")
    transition(tmp_path, "alpha", TicketState.DONE, by="sys")
    assert get_state(tmp_path, "alpha") == TicketState.DONE
    chain_transition(tmp_path, "alpha", TicketState.PENDING, by="op")
    assert get_state(tmp_path, "alpha") == TicketState.PENDING
    states = [r.to_state for r in transitions_for(tmp_path, "alpha")]
    assert TicketState.QUEUED in states  # intermediate hop

    # ABORTED → PENDING (single legal step)
    transition(tmp_path, "beta", TicketState.QUEUED, by="op")
    transition(tmp_path, "beta", TicketState.IN_PROGRESS, by="sys")
    transition(tmp_path, "beta", TicketState.ABORTED, by="sys")
    chain_transition(tmp_path, "beta", TicketState.PENDING, by="op")
    assert get_state(tmp_path, "beta") == TicketState.PENDING

    # No-record → QUEUED via PENDING back-fill
    chain_transition(tmp_path, "gamma", TicketState.QUEUED, by="op")
    assert get_state(tmp_path, "gamma") == TicketState.QUEUED

    # Idempotent
    chain_transition(tmp_path, "gamma", TicketState.QUEUED, by="op")
    assert get_state(tmp_path, "gamma") == TicketState.QUEUED


def test_chain_transition_done_via_queued_in_progress(
    tmp_path: Path,
) -> None:
    """Mark-Ready bulk op: a PENDING ticket reaches DONE via
    QUEUED → IN_PROGRESS → DONE."""
    from wonderland.ticket_lifecycle import (
        TicketState,
        chain_transition,
        get_state,
        transitions_for,
    )

    chain_transition(tmp_path, "alpha", TicketState.DONE, by="op")
    assert get_state(tmp_path, "alpha") == TicketState.DONE
    states = [r.to_state for r in transitions_for(tmp_path, "alpha")]
    # PENDING (back-fill) → QUEUED → IN_PROGRESS → DONE
    assert states == [
        TicketState.PENDING,
        TicketState.QUEUED,
        TicketState.IN_PROGRESS,
        TicketState.DONE,
    ]


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


# --- md status propagation (substrate bug 85aaee91 fix) ---


def test_transition_propagates_state_to_md_status_field(
    tmp_path: Path,
) -> None:
    """Ledger transitions cascade into the ticket .md file's
    ``**Status:**`` field. Without this, operators inspecting
    tickets directly saw stale state (md always said `open`
    regardless of lifecycle state); pipeline_runner correctly
    used the ledger but the divergence confused operators and
    leaked into the dashboard (substrate bug 85aaee91)."""
    import re
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.ticket import TicketPayload, TicketRegistry
    from wonderland.ticket_lifecycle import (
        TicketState,
        back_fill_state,
        transition,
    )

    # Story for the ticket to anchor to (phantom-citation filter).
    StoryRegistry(tmp_path).write(StoryPayload(
        title="Real story",
        persona="p", situation="x",
        need="As p I want y so z.",
        acceptance=["a"], tier="core",
        confusion_flags=["c"],
    ))
    record = TicketRegistry(tmp_path).write(TicketPayload(
        title="A ticket",
        owner="tweedledum",
        tier="v1",
        estimate="1d",
        description="d",
        sources=["real-story"],
    ))

    def md_status() -> str:
        text = record.path.read_text(encoding="utf-8")
        m = re.search(r"^\*\*Status:\*\*\s*(\S+)", text, re.MULTILINE)
        assert m, "Status field missing from ticket md"
        return m.group(1)

    # Fresh ticket: status open per the default TicketPayload.status.
    assert md_status() == "open"

    # Walk the lifecycle: each transition should cascade to md.
    back_fill_state(tmp_path, record.slug, TicketState.PENDING)
    assert md_status() == "open"  # PENDING and QUEUED both render as 'open'

    transition(tmp_path, record.slug, TicketState.QUEUED, by="operator")
    assert md_status() == "open"

    transition(tmp_path, record.slug, TicketState.IN_PROGRESS, by="system")
    assert md_status() == "in_flight"

    transition(tmp_path, record.slug, TicketState.DONE, by="system")
    assert md_status() == "done"


def test_transition_md_propagation_is_best_effort(tmp_path: Path) -> None:
    """Propagation failures don't break the primary ledger write
    contract. The ledger remains canonical even if the md update
    can't land (deleted file, permissions, etc)."""
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.ticket import TicketPayload, TicketRegistry
    from wonderland.ticket_lifecycle import (
        TicketState,
        back_fill_state,
        get_state,
        transition,
    )

    StoryRegistry(tmp_path).write(StoryPayload(
        title="Real story",
        persona="p", situation="x",
        need="As p I want y so z.",
        acceptance=["a"], tier="core",
        confusion_flags=["c"],
    ))
    record = TicketRegistry(tmp_path).write(TicketPayload(
        title="Doomed ticket",
        owner="tweedledee",
        tier="v1",
        estimate="1d",
        description="d",
        sources=["real-story"],
    ))
    back_fill_state(tmp_path, record.slug, TicketState.PENDING)
    transition(tmp_path, record.slug, TicketState.QUEUED, by="operator")

    # Delete the md before transitioning — propagation will silently
    # skip, but the ledger must still record the transition.
    record.path.unlink()
    transition(tmp_path, record.slug, TicketState.IN_PROGRESS, by="system")
    assert get_state(tmp_path, record.slug) == TicketState.IN_PROGRESS


def test_tombstone_aborts_from_any_state_bypassing_legal_gate(
    tmp_path: Path,
) -> None:
    """A pruned ticket can be QUEUED — and QUEUED→ABORTED is NOT a legal
    transition. tombstone() bypasses the gate so the ledger reflects the
    deleted artifact instead of leaving a phantom QUEUED entry."""
    transition(tmp_path, "ticket-x", TicketState.QUEUED, by="operator")
    rec = tombstone(tmp_path, "ticket-x", by="operator", notes="pruned")
    assert rec is not None
    assert get_state(tmp_path, "ticket-x") == TicketState.ABORTED


def test_tombstone_noop_on_unrecorded_or_already_aborted(
    tmp_path: Path,
) -> None:
    assert tombstone(tmp_path, "never-existed", by="op") is None
    transition(tmp_path, "ticket-y", TicketState.QUEUED, by="op")
    assert tombstone(tmp_path, "ticket-y", by="op") is not None
    assert tombstone(tmp_path, "ticket-y", by="op") is None  # already aborted


def test_sweep_tombstones_phantom_leaves_real_and_terminal(
    tmp_path: Path,
) -> None:
    """The phantom sweep tombstones a non-terminal ledger state whose
    artifact is gone, but leaves (a) a real ticket whose artifact exists
    and (b) a DONE/terminal ledger state (relabelling it ABORTED would
    misstate history)."""
    from wonderland.ticket import TicketPayload, TicketRegistry, TicketTier

    reg = TicketRegistry(tmp_path)
    real = reg.write(
        TicketPayload(
            title="Real ticket with an artifact",
            owner="tweedledee",
            tier=TicketTier.V1,
            estimate="1d",
            description="x",
        )
    )
    transition(tmp_path, real.slug, TicketState.QUEUED, by="op")
    # phantom: QUEUED in the ledger, no artifact on disk
    transition(tmp_path, "phantom-queued", TicketState.QUEUED, by="op")
    # terminal phantom: DONE, no artifact — out of sweep scope
    transition(tmp_path, "done-phantom", TicketState.QUEUED, by="op")
    transition(tmp_path, "done-phantom", TicketState.IN_PROGRESS, by="op")
    transition(tmp_path, "done-phantom", TicketState.DONE, by="op")

    swept = tombstone_orphaned_ticket_states(tmp_path, by="sweep")

    assert swept == ["phantom-queued"]
    assert get_state(tmp_path, "phantom-queued") == TicketState.ABORTED
    assert get_state(tmp_path, real.slug) == TicketState.QUEUED
    assert get_state(tmp_path, "done-phantom") == TicketState.DONE
    # idempotent — a second sweep finds nothing new
    assert tombstone_orphaned_ticket_states(tmp_path, by="sweep") == []
