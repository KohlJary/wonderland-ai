"""Tests for the feature lifecycle data layer (P12 T85)."""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.feature_lifecycle import (
    FEATURE_STATES_FILENAME,
    FeatureState,
    IllegalTransitionError,
    LEGAL_TRANSITIONS,
    TransitionRecord,
    all_transitions,
    get_state,
    list_features_in_state,
    transition,
    transitions_for,
)


# --- FeatureState enum + LEGAL_TRANSITIONS shape ---


class TestFeatureStateEnum:
    def test_all_documented_states_exist(self) -> None:
        names = {s.value for s in FeatureState}
        assert names == {
            "proposed", "in_design", "designed", "queued",
            "in_progress", "ready_for_review", "verified", "rejected",
        }

    def test_legal_transitions_covers_every_state(self) -> None:
        """LEGAL_TRANSITIONS must have an entry for every state +
        for the None initial state. Missing entries would manifest
        as silent rejections."""
        keys = set(LEGAL_TRANSITIONS.keys())
        expected = set(FeatureState) | {None}
        assert keys == expected

    def test_initial_only_into_proposed(self) -> None:
        """The only legal first transition is into proposed."""
        assert LEGAL_TRANSITIONS[None] == frozenset({FeatureState.PROPOSED})

    def test_terminal_states_have_no_outbound(self) -> None:
        """Verified and rejected are terminal — no further legal
        transitions exit them."""
        assert LEGAL_TRANSITIONS[FeatureState.VERIFIED] == frozenset()
        assert LEGAL_TRANSITIONS[FeatureState.REJECTED] == frozenset()

    def test_designed_can_go_to_queued_or_rejected(self) -> None:
        """Operator can either queue for implementation or reject at
        design review. Both are core P12 paths."""
        legal = LEGAL_TRANSITIONS[FeatureState.DESIGNED]
        assert FeatureState.QUEUED in legal
        assert FeatureState.REJECTED in legal

    def test_designed_can_revert_to_in_design(self) -> None:
        """Operator can send a feature back to in_design for
        re-decomposition via the tdd-decompose workflow.
        Validation5 surfaced this — features 4 + 5 had zero
        tickets attributed (M3 slug drift) and needed a way to
        regenerate tickets without rerunning the full design
        pipeline. ``designed → in_design`` is the operator's
        re-design trigger; tdd-decompose then iterates M3+M3.5
        over features in in_design and transitions them back to
        designed."""
        legal = LEGAL_TRANSITIONS[FeatureState.DESIGNED]
        assert FeatureState.IN_DESIGN in legal

    def test_queued_can_revert_to_designed(self) -> None:
        """Un-queue: operator changes mind before implementation
        starts. designed ⇄ queued is a 2-way edge."""
        assert FeatureState.DESIGNED in LEGAL_TRANSITIONS[FeatureState.QUEUED]


# --- TransitionRecord shape ---


class TestTransitionRecord:
    def test_minimal_construction(self) -> None:
        record = TransitionRecord(
            feature_slug="balance-dashboard",
            to_state=FeatureState.PROPOSED,
            by="white_rabbit",
        )
        assert record.feature_slug == "balance-dashboard"
        assert record.from_state is None
        assert record.to_state == FeatureState.PROPOSED
        assert record.by == "white_rabbit"
        assert record.notes is None

    def test_round_trips_through_json(self) -> None:
        original = TransitionRecord(
            feature_slug="x",
            from_state=FeatureState.DESIGNED,
            to_state=FeatureState.QUEUED,
            by="operator",
            notes="batched for tomorrow's run",
        )
        roundtripped = TransitionRecord.model_validate_json(
            original.model_dump_json()
        )
        assert roundtripped == original

    def test_slug_must_be_non_empty(self) -> None:
        with pytest.raises(ValueError):
            TransitionRecord(
                feature_slug="",
                to_state=FeatureState.PROPOSED,
                by="x",
            )

    def test_by_must_be_non_empty(self) -> None:
        with pytest.raises(ValueError):
            TransitionRecord(
                feature_slug="x",
                to_state=FeatureState.PROPOSED,
                by="",
            )


# --- transition() / get_state() basic flow ---


def _make_feature_and_tickets(
    tmp_path: Path,
    feature_slug: str,
    ticket_slugs: list[str],
) -> None:
    """Write feature + ticket markdown files so
    ``_ticket_to_feature_map`` resolves the parents. Used by the
    derivation tests below."""
    wonderland = tmp_path / ".wonderland"
    (wonderland / "features").mkdir(parents=True, exist_ok=True)
    (wonderland / "tickets").mkdir(parents=True, exist_ok=True)
    (wonderland / "features" / f"feature-001-{feature_slug}.md").write_text(
        f"## Feature 001: {feature_slug}\n",
        encoding="utf-8",
    )
    for idx, slug in enumerate(ticket_slugs, start=1):
        (
            wonderland / "tickets" / f"ticket-{idx:03d}-{slug}.md"
        ).write_text(
            f"## Ticket {idx:03d}: {slug}\n\n**Sources:** {feature_slug}\n",
            encoding="utf-8",
        )


class TestDerivedState:
    """Post-ticket feature state is rolled up from the ticket
    lifecycle, not read verbatim from the log. Pre-ticket states
    (proposed/in_design/designed) and operator terminals
    (verified/rejected) stay in the log."""

    def test_no_tickets_returns_log_state(self, tmp_path: Path) -> None:
        """Feature in ``designed`` per the log, no tickets yet
        (M3 hasn't decomposed). Derivation returns None, log wins."""
        slug = "alpha"
        _make_feature_and_tickets(tmp_path, slug, ticket_slugs=[])
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        assert get_state(tmp_path, slug) == FeatureState.DESIGNED

    def test_all_tickets_pending_returns_log_state(
        self, tmp_path: Path
    ) -> None:
        """Tickets exist but none have an operator-touched state —
        feature stays in its pre-ticket state."""
        from wonderland.ticket_lifecycle import (
            TicketState,
            transition as ticket_transition,
        )

        slug = "alpha"
        _make_feature_and_tickets(
            tmp_path, slug, ticket_slugs=["a", "b"]
        )
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        ticket_transition(tmp_path, "a", TicketState.PENDING, by="system")
        ticket_transition(tmp_path, "b", TicketState.PENDING, by="system")
        assert get_state(tmp_path, slug) == FeatureState.DESIGNED

    def test_any_ticket_queued_derives_queued(
        self, tmp_path: Path
    ) -> None:
        from wonderland.ticket_lifecycle import (
            TicketState,
            transition as ticket_transition,
        )

        slug = "alpha"
        _make_feature_and_tickets(
            tmp_path, slug, ticket_slugs=["a", "b"]
        )
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        ticket_transition(tmp_path, "a", TicketState.QUEUED, by="operator")
        assert get_state(tmp_path, slug) == FeatureState.QUEUED

    def test_any_ticket_in_progress_derives_in_progress(
        self, tmp_path: Path
    ) -> None:
        from wonderland.ticket_lifecycle import (
            TicketState,
            transition as ticket_transition,
        )

        slug = "alpha"
        _make_feature_and_tickets(
            tmp_path, slug, ticket_slugs=["a", "b"]
        )
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        ticket_transition(tmp_path, "a", TicketState.QUEUED, by="operator")
        ticket_transition(tmp_path, "a", TicketState.IN_PROGRESS, by="system")
        assert get_state(tmp_path, slug) == FeatureState.IN_PROGRESS

    def test_aborted_ticket_still_in_progress(
        self, tmp_path: Path
    ) -> None:
        """ABORTED rolls up to IN_PROGRESS — the feature still has
        work in flight from the operator's perspective (just stalled
        and owing a retry call). The ticket-level ⚠ badge carries
        the "needs attention" signal."""
        from wonderland.ticket_lifecycle import (
            TicketState,
            transition as ticket_transition,
        )

        slug = "alpha"
        _make_feature_and_tickets(
            tmp_path, slug, ticket_slugs=["a", "b"]
        )
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        ticket_transition(tmp_path, "a", TicketState.QUEUED, by="operator")
        ticket_transition(tmp_path, "a", TicketState.IN_PROGRESS, by="system")
        ticket_transition(tmp_path, "a", TicketState.ABORTED, by="system")
        assert get_state(tmp_path, slug) == FeatureState.IN_PROGRESS

    def test_all_tickets_done_derives_ready_for_review(
        self, tmp_path: Path
    ) -> None:
        from wonderland.ticket_lifecycle import (
            TicketState,
            transition as ticket_transition,
        )

        slug = "alpha"
        _make_feature_and_tickets(
            tmp_path, slug, ticket_slugs=["a", "b"]
        )
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        for t in ("a", "b"):
            ticket_transition(tmp_path, t, TicketState.QUEUED, by="operator")
            ticket_transition(tmp_path, t, TicketState.IN_PROGRESS, by="system")
            ticket_transition(tmp_path, t, TicketState.DONE, by="system")
        assert get_state(tmp_path, slug) == FeatureState.READY_FOR_REVIEW

    def test_mixed_done_and_pending_is_in_progress(
        self, tmp_path: Path
    ) -> None:
        """Partial work shipped, more pending — feature stays
        in_progress. Operator decides whether to queue the rest or
        verify what's there."""
        from wonderland.ticket_lifecycle import (
            TicketState,
            transition as ticket_transition,
        )

        slug = "alpha"
        _make_feature_and_tickets(
            tmp_path, slug, ticket_slugs=["a", "b"]
        )
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        ticket_transition(tmp_path, "a", TicketState.QUEUED, by="operator")
        ticket_transition(tmp_path, "a", TicketState.IN_PROGRESS, by="system")
        ticket_transition(tmp_path, "a", TicketState.DONE, by="system")
        # ticket "b" untouched (no record → PENDING-by-default).
        assert get_state(tmp_path, slug) == FeatureState.IN_PROGRESS

    def test_legacy_log_post_ticket_entries_ignored(
        self, tmp_path: Path
    ) -> None:
        """A legacy ``feature-states.jsonl`` from before the
        derivation layer may carry post-ticket entries (queued,
        in_progress, ready_for_review). Those are ignored when
        tickets exist with meaningful state — derivation wins."""
        from wonderland.ticket_lifecycle import (
            TicketState,
            transition as ticket_transition,
        )

        slug = "alpha"
        _make_feature_and_tickets(
            tmp_path, slug, ticket_slugs=["a"]
        )
        # Legacy log all the way through ready_for_review.
        for st in (
            FeatureState.PROPOSED,
            FeatureState.IN_DESIGN,
            FeatureState.DESIGNED,
            FeatureState.QUEUED,
            FeatureState.IN_PROGRESS,
            FeatureState.READY_FOR_REVIEW,
        ):
            transition(tmp_path, slug, st, by="legacy")
        # Ticket says QUEUED (operator just re-queued for retry).
        ticket_transition(tmp_path, "a", TicketState.QUEUED, by="operator")
        # Derivation wins over the legacy ready_for_review log entry.
        assert get_state(tmp_path, slug) == FeatureState.QUEUED

    def test_verified_terminal_overrides_derivation(
        self, tmp_path: Path
    ) -> None:
        """Verified is final; the substrate doesn't auto-revert it
        if the operator later mutates a ticket. (E.g., operator
        verified the feature; later re-queues a ticket as a
        side-quest. Feature stays verified — the operator can
        explicitly reject if they want to un-verify.)"""
        from wonderland.ticket_lifecycle import (
            TicketState,
            transition as ticket_transition,
        )

        slug = "alpha"
        _make_feature_and_tickets(
            tmp_path, slug, ticket_slugs=["a"]
        )
        for st in (
            FeatureState.PROPOSED,
            FeatureState.IN_DESIGN,
            FeatureState.DESIGNED,
            FeatureState.QUEUED,
            FeatureState.IN_PROGRESS,
            FeatureState.READY_FOR_REVIEW,
            FeatureState.VERIFIED,
        ):
            transition(tmp_path, slug, st, by="legacy")
        ticket_transition(tmp_path, "a", TicketState.QUEUED, by="operator")
        assert get_state(tmp_path, slug) == FeatureState.VERIFIED


class TestTransitionAndGetState:
    def test_initial_transition_to_proposed(self, tmp_path: Path) -> None:
        record = transition(
            tmp_path, "alpha", FeatureState.PROPOSED, by="white_rabbit"
        )
        assert record.from_state is None
        assert record.to_state == FeatureState.PROPOSED
        assert get_state(tmp_path, "alpha") == FeatureState.PROPOSED

    def test_get_state_none_for_unknown_feature(self, tmp_path: Path) -> None:
        assert get_state(tmp_path, "ghost") is None

    def test_full_happy_path(self, tmp_path: Path) -> None:
        """proposed → in_design → designed → queued → in_progress →
        ready_for_review → verified."""
        slug = "alpha"
        transitions = [
            (FeatureState.PROPOSED, "white_rabbit"),
            (FeatureState.IN_DESIGN, "tweedledee"),
            (FeatureState.DESIGNED, "system"),
            (FeatureState.QUEUED, "operator"),
            (FeatureState.IN_PROGRESS, "system"),
            (FeatureState.READY_FOR_REVIEW, "system"),
            (FeatureState.VERIFIED, "operator"),
        ]
        for to_state, by in transitions:
            transition(tmp_path, slug, to_state, by=by)
        assert get_state(tmp_path, slug) == FeatureState.VERIFIED
        history = transitions_for(tmp_path, slug)
        assert len(history) == 7

    def test_rejection_at_design_review(self, tmp_path: Path) -> None:
        slug = "alpha"
        transition(tmp_path, slug, FeatureState.PROPOSED, by="white_rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="caterpillar")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        transition(
            tmp_path,
            slug,
            FeatureState.REJECTED,
            by="operator",
            notes="Plaid auth handling is hand-waved; redesign first",
        )
        assert get_state(tmp_path, slug) == FeatureState.REJECTED
        # Notes preserved for cross-run continuity (T90)
        history = transitions_for(tmp_path, slug)
        assert history[-1].notes == (
            "Plaid auth handling is hand-waved; redesign first"
        )


# --- Illegal transitions ---


class TestIllegalTransitions:
    def test_initial_must_be_proposed(self, tmp_path: Path) -> None:
        with pytest.raises(IllegalTransitionError, match="initial"):
            transition(
                tmp_path, "alpha", FeatureState.DESIGNED, by="cheshire_cat"
            )

    def test_skip_state_rejected(self, tmp_path: Path) -> None:
        """Cannot jump from proposed straight to designed — must
        pass through in_design."""
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        with pytest.raises(IllegalTransitionError, match="proposed"):
            transition(
                tmp_path, "alpha", FeatureState.DESIGNED, by="cheshire_cat"
            )

    def test_terminal_state_blocks_further_moves(
        self, tmp_path: Path
    ) -> None:
        """Verified and rejected are terminal — no transition out."""
        slug = "alpha"
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")
        transition(tmp_path, slug, FeatureState.QUEUED, by="operator")
        transition(tmp_path, slug, FeatureState.IN_PROGRESS, by="system")
        transition(tmp_path, slug, FeatureState.READY_FOR_REVIEW, by="system")
        transition(tmp_path, slug, FeatureState.VERIFIED, by="operator")
        with pytest.raises(IllegalTransitionError, match="terminal"):
            transition(
                tmp_path, slug, FeatureState.QUEUED, by="operator"
            )

    def test_error_message_includes_legal_options(
        self, tmp_path: Path
    ) -> None:
        """The illegal-transition error tells the operator what
        moves WOULD be legal — useful for debugging."""
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        try:
            transition(
                tmp_path, "alpha", FeatureState.VERIFIED, by="operator"
            )
        except IllegalTransitionError as exc:
            msg = str(exc)
            # Legal from proposed: in_design, rejected
            assert "in_design" in msg
            assert "rejected" in msg
        else:
            pytest.fail("expected IllegalTransitionError")


# --- list_features_in_state ---


class TestListFeaturesInState:
    def test_returns_only_features_currently_in_state(
        self, tmp_path: Path
    ) -> None:
        # alpha: proposed → in_design (current state: in_design)
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "alpha", FeatureState.IN_DESIGN, by="rabbit")
        # beta: still proposed
        transition(tmp_path, "beta", FeatureState.PROPOSED, by="rabbit")
        # gamma: proposed → in_design → designed (current: designed)
        transition(tmp_path, "gamma", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "gamma", FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, "gamma", FeatureState.DESIGNED, by="system")

        proposed = list_features_in_state(tmp_path, FeatureState.PROPOSED)
        in_design = list_features_in_state(tmp_path, FeatureState.IN_DESIGN)
        designed = list_features_in_state(tmp_path, FeatureState.DESIGNED)

        assert proposed == ["beta"]
        assert in_design == ["alpha"]
        assert designed == ["gamma"]

    def test_alphabetical_order(self, tmp_path: Path) -> None:
        transition(tmp_path, "charlie", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "bravo", FeatureState.PROPOSED, by="rabbit")
        result = list_features_in_state(tmp_path, FeatureState.PROPOSED)
        assert result == ["alpha", "bravo", "charlie"]

    def test_empty_when_no_features_in_state(
        self, tmp_path: Path
    ) -> None:
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        assert list_features_in_state(tmp_path, FeatureState.VERIFIED) == []


# --- Persistence ---


class TestPersistence:
    def test_creates_registry_file_lazily(self, tmp_path: Path) -> None:
        path = tmp_path / ".wonderland" / FEATURE_STATES_FILENAME
        assert not path.exists()
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        assert path.is_file()

    def test_append_only_log_preserves_history(
        self, tmp_path: Path
    ) -> None:
        """Each transition lands as a new line; prior lines stay
        intact. Reading the log gives full audit history."""
        slug = "alpha"
        transition(tmp_path, slug, FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, slug, FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, slug, FeatureState.DESIGNED, by="system")

        path = tmp_path / ".wonderland" / FEATURE_STATES_FILENAME
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3

    def test_all_transitions_in_chronological_order(
        self, tmp_path: Path
    ) -> None:
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "beta", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "alpha", FeatureState.IN_DESIGN, by="rabbit")

        history = all_transitions(tmp_path)
        assert len(history) == 3
        assert history[0].feature_slug == "alpha"
        assert history[0].to_state == FeatureState.PROPOSED
        assert history[1].feature_slug == "beta"
        assert history[2].feature_slug == "alpha"
        assert history[2].to_state == FeatureState.IN_DESIGN

    def test_malformed_lines_skipped_silently(
        self, tmp_path: Path
    ) -> None:
        """A partial write during a crash shouldn't corrupt the
        whole log. Malformed lines get skipped; valid ones still
        load."""
        path = tmp_path / ".wonderland" / FEATURE_STATES_FILENAME
        path.parent.mkdir(parents=True)
        # Mix of valid + malformed
        record = TransitionRecord(
            feature_slug="alpha",
            to_state=FeatureState.PROPOSED,
            by="rabbit",
        )
        path.write_text(
            "not json at all {{\n"
            + record.model_dump_json() + "\n"
            + '{"feature_slug": "missing_required_fields"}\n'
            + "\n",  # blank line
            encoding="utf-8",
        )
        history = all_transitions(tmp_path)
        assert len(history) == 1
        assert history[0].feature_slug == "alpha"

    def test_empty_registry_returns_empty_list(
        self, tmp_path: Path
    ) -> None:
        assert all_transitions(tmp_path) == []

    def test_transitions_for_specific_feature(
        self, tmp_path: Path
    ) -> None:
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "beta", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "alpha", FeatureState.IN_DESIGN, by="rabbit")
        transition(tmp_path, "alpha", FeatureState.DESIGNED, by="system")

        alpha_history = transitions_for(tmp_path, "alpha")
        beta_history = transitions_for(tmp_path, "beta")

        assert len(alpha_history) == 3
        assert len(beta_history) == 1
        assert all(r.feature_slug == "alpha" for r in alpha_history)


# --- Sanity checks for state machine completeness ---


class TestBackFillState:
    """back_fill_state bypasses normal transition validation —
    used for migrating pre-T85 features into the lifecycle."""

    def test_back_fill_records_state_directly(
        self, tmp_path: Path
    ) -> None:
        from wonderland.feature_lifecycle import back_fill_state

        # No prior state — back-fill straight to designed (a state
        # the normal transition() wouldn't allow as initial).
        record = back_fill_state(tmp_path, "alpha", FeatureState.DESIGNED)
        assert record.to_state == FeatureState.DESIGNED
        assert record.from_state is None
        assert record.by == "system_backfill"
        # State is now queryable via the normal API.
        assert get_state(tmp_path, "alpha") == FeatureState.DESIGNED

    def test_back_fill_refuses_when_state_exists(
        self, tmp_path: Path
    ) -> None:
        from wonderland.feature_lifecycle import back_fill_state

        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        with pytest.raises(ValueError, match="already has a recorded state"):
            back_fill_state(tmp_path, "alpha", FeatureState.DESIGNED)

    def test_back_filled_feature_can_transition_normally(
        self, tmp_path: Path
    ) -> None:
        """After back-fill to designed, normal transitions work
        (designed → queued → in_progress etc.)."""
        from wonderland.feature_lifecycle import back_fill_state

        back_fill_state(tmp_path, "alpha", FeatureState.DESIGNED)
        # Now operator can queue it normally
        transition(tmp_path, "alpha", FeatureState.QUEUED, by="operator")
        assert get_state(tmp_path, "alpha") == FeatureState.QUEUED


class TestStateMachineCoherence:
    def test_every_non_terminal_state_has_outbound_transitions(
        self,
    ) -> None:
        """Non-terminal states must permit at least one move out
        (otherwise features get stuck and need a manual
        registry-edit to recover)."""
        terminal = {FeatureState.VERIFIED, FeatureState.REJECTED}
        for state in FeatureState:
            if state in terminal:
                continue
            assert LEGAL_TRANSITIONS[state], (
                f"non-terminal state {state.value} has no outbound moves"
            )

    def test_proposed_eventually_reaches_designed(self) -> None:
        """Sanity: there's a path from PROPOSED to DESIGNED through
        only legal transitions."""
        # proposed → in_design → designed
        assert FeatureState.IN_DESIGN in LEGAL_TRANSITIONS[FeatureState.PROPOSED]
        assert FeatureState.DESIGNED in LEGAL_TRANSITIONS[FeatureState.IN_DESIGN]

    def test_designed_eventually_reaches_verified(self) -> None:
        """Sanity: there's a path from DESIGNED to VERIFIED."""
        # designed → queued → in_progress → ready_for_review → verified
        assert FeatureState.QUEUED in LEGAL_TRANSITIONS[FeatureState.DESIGNED]
        assert FeatureState.IN_PROGRESS in LEGAL_TRANSITIONS[FeatureState.QUEUED]
        assert FeatureState.READY_FOR_REVIEW in LEGAL_TRANSITIONS[FeatureState.IN_PROGRESS]
        assert FeatureState.VERIFIED in LEGAL_TRANSITIONS[FeatureState.READY_FOR_REVIEW]
