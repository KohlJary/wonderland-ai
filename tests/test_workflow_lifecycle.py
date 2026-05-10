"""Tests for T86 (input filter) + T87 (output transitions) — the
workflow primitives that bridge feature lifecycle to workflow YAML.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from wonderland.feature_lifecycle import (
    FeatureState,
    get_state,
    transition,
    transitions_for,
)
from wonderland.workflow import (
    Meeting,
    _apply_emission_transition_for_utterance,
    _apply_post_meeting_transitions,
)


# --- Meeting model: new fields ---


class TestMeetingLifecycleFields:
    def test_iterate_only_in_states_default_none(self) -> None:
        m = Meeting(id="m", label="M", goal="g", roster=["alice"])
        assert m.iterate_only_in_states is None

    def test_transition_emitted_to_default_none(self) -> None:
        m = Meeting(id="m", label="M", goal="g", roster=["alice"])
        assert m.transition_emitted_to is None

    def test_transition_iteration_to_default_none(self) -> None:
        m = Meeting(id="m", label="M", goal="g", roster=["alice"])
        assert m.transition_iteration_to is None

    def test_iterate_only_in_states_accepts_list(self) -> None:
        m = Meeting(
            id="implementation",
            label="M5",
            goal="ship",
            roster=["tweedledee"],
            per_item="ticket",
            iterate_only_in_states=["queued"],
        )
        assert m.iterate_only_in_states == ["queued"]

    def test_yaml_field_validates(self) -> None:
        m = Meeting(
            id="m4",
            label="M4",
            goal="g",
            roster=["mad_hatter"],
            transition_iteration_to="designed",
        )
        assert m.transition_iteration_to == "designed"


# --- T87 _apply_post_meeting_transitions ---


def _runner_with_root(tmp_path: Path) -> SimpleNamespace:
    """Minimal runner stub for the transition helper. Only needs
    project_root attribute."""
    return SimpleNamespace(project_root=tmp_path)


def _feature_utterance(slug: str, title: str = ""):
    """Synthesize a feature-emitting utterance for the helper to scan."""
    from wonderland.utterance import (
        AgentIdentity,
        Artifact,
        SpeechAct,
        Utterance,
        UtteranceContent,
    )

    return Utterance(
        thread_id="composition",
        speaker=AgentIdentity(name="white_rabbit", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.FEATURE,
        content=UtteranceContent(
            body=f"Feature: {slug}",
            artifacts=[
                Artifact(
                    kind="feature",
                    payload={"slug": slug, "title": title or slug},
                ),
            ],
        ),
    )


class TestApplyPostMeetingTransitions:
    def test_transition_emitted_fires_for_emitted_features(
        self, tmp_path: Path
    ) -> None:
        """M2.5-style: meeting emits feature artifacts; per-utterance
        helper transitions each one to transition_emitted_to.

        transition_emitted_to fires per-utterance (not post-MeetingEnd)
        to close the dashboard-backfill race — see workflow.py docstring
        on _apply_emission_transition_for_utterance.
        """
        meeting = Meeting(
            id="composition",
            label="M2.5",
            goal="g",
            roster=["white_rabbit"],
            transition_emitted_to="proposed",
        )
        runner = _runner_with_root(tmp_path)
        emissions = [
            _feature_utterance("alpha"),
            _feature_utterance("bravo"),
        ]
        for u in emissions:
            _apply_emission_transition_for_utterance(
                meeting=meeting, runner=runner, utterance=u
            )
        assert get_state(tmp_path, "alpha") == FeatureState.PROPOSED
        assert get_state(tmp_path, "bravo") == FeatureState.PROPOSED

    def test_transition_emitted_idempotent_on_existing_features(
        self, tmp_path: Path
    ) -> None:
        """Re-running M2.5 on a project where features already moved
        past 'proposed' should NOT corrupt their state — illegal
        transition gets caught silently."""
        # alpha already moved past proposed
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "alpha", FeatureState.IN_DESIGN, by="rabbit")

        meeting = Meeting(
            id="composition",
            label="M2.5",
            goal="g",
            roster=["white_rabbit"],
            transition_emitted_to="proposed",
        )
        runner = _runner_with_root(tmp_path)
        _apply_emission_transition_for_utterance(
            meeting=meeting,
            runner=runner,
            utterance=_feature_utterance("alpha"),
        )
        # alpha stays where it was — not corrupted.
        assert get_state(tmp_path, "alpha") == FeatureState.IN_DESIGN

    def test_transition_emitted_skips_non_feature_artifacts(
        self, tmp_path: Path
    ) -> None:
        """Only feature-kind artifacts trigger transitions; tickets
        / contracts / scenarios in the same emission are ignored."""
        from wonderland.utterance import (
            AgentIdentity,
            Artifact,
            SpeechAct,
            Utterance,
            UtteranceContent,
        )

        ticket_emission = Utterance(
            thread_id="composition",
            speaker=AgentIdentity(
                name="white_rabbit", constitution_version="0.1"
            ),
            addressed_to="caucus",
            speech_act=SpeechAct.TICKET,
            content=UtteranceContent(
                body="ticket body",
                artifacts=[
                    Artifact(kind="ticket", payload={"slug": "t-1"}),
                ],
            ),
        )
        meeting = Meeting(
            id="m",
            label="M",
            goal="g",
            roster=["white_rabbit"],
            transition_emitted_to="proposed",
        )
        _apply_emission_transition_for_utterance(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            utterance=ticket_emission,
        )
        # No feature transitions happened.
        assert get_state(tmp_path, "t-1") is None

    def test_transition_iteration_fires_for_current_item(
        self, tmp_path: Path
    ) -> None:
        """M4-style: per_item meeting; iteration's feature transitions
        to the named state on completion."""
        # Set up: alpha is in_design (M3 already ran)
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")
        transition(tmp_path, "alpha", FeatureState.IN_DESIGN, by="cheshire_cat")

        meeting = Meeting(
            id="test-scenarios",
            label="M4",
            goal="g",
            roster=["mad_hatter"],
            per_item="feature",
            transition_iteration_to="designed",
        )
        runner = _runner_with_root(tmp_path)
        _apply_post_meeting_transitions(
            meeting=meeting,
            runner=runner,
            new_utterances=[],  # M4 emits scenarios, not features
            current_item_slug="alpha",
        )
        assert get_state(tmp_path, "alpha") == FeatureState.DESIGNED

    def test_transition_iteration_idempotent_when_target_illegal(
        self, tmp_path: Path
    ) -> None:
        """Per_item meeting fires transition_iteration_to but the
        feature is already in a terminal/non-allowed state — illegal
        transition gets silently swallowed; feature stays put.

        Setup: alpha is rejected (terminal). M4 tries to transition
        it back to 'designed' — illegal, no-op."""
        for state, by in [
            (FeatureState.PROPOSED, "r"),
            (FeatureState.REJECTED, "operator"),
        ]:
            transition(tmp_path, "alpha", state, by=by)

        meeting = Meeting(
            id="test-scenarios",
            label="M4",
            goal="g",
            roster=["mad_hatter"],
            per_item="feature",
            transition_iteration_to="designed",
        )
        _apply_post_meeting_transitions(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[],
            current_item_slug="alpha",
        )
        # Stays at rejected — terminal state's outbound is empty;
        # illegal transition silently swallowed.
        assert get_state(tmp_path, "alpha") == FeatureState.REJECTED

    def test_transition_iteration_un_queue_is_legal(
        self, tmp_path: Path
    ) -> None:
        """Edge case: queued → designed IS legal (un-queue path).
        If a workflow declares transition_iteration_to=designed and
        the feature was already queued, the un-queue actually fires.
        Useful for re-running design on a queued feature: design
        run un-queues automatically so operator re-evaluates the
        new design before re-queueing."""
        for state, by in [
            (FeatureState.PROPOSED, "r"),
            (FeatureState.IN_DESIGN, "r"),
            (FeatureState.DESIGNED, "system"),
            (FeatureState.QUEUED, "operator"),
        ]:
            transition(tmp_path, "alpha", state, by=by)

        meeting = Meeting(
            id="test-scenarios",
            label="M4",
            goal="g",
            roster=["mad_hatter"],
            per_item="feature",
            transition_iteration_to="designed",
        )
        _apply_post_meeting_transitions(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[],
            current_item_slug="alpha",
        )
        # Un-queue: queued → designed is legal.
        assert get_state(tmp_path, "alpha") == FeatureState.DESIGNED

    def test_transition_skipped_when_no_project_root(
        self, tmp_path: Path
    ) -> None:
        """FakeRunner test fixtures (no project_root attribute)
        don't break the workflow — transitions just no-op."""
        meeting = Meeting(
            id="composition",
            label="M2.5",
            goal="g",
            roster=["white_rabbit"],
            transition_emitted_to="proposed",
        )
        # SimpleNamespace without project_root attribute
        runner_no_root = SimpleNamespace()
        # Should not raise, should be a no-op.
        _apply_post_meeting_transitions(
            meeting=meeting,
            runner=runner_no_root,
            new_utterances=[_feature_utterance("alpha")],
            current_item_slug=None,
        )

    def test_no_transition_fields_no_op(self, tmp_path: Path) -> None:
        """Meetings without transition_emitted_to or
        transition_iteration_to set leave feature state untouched."""
        meeting = Meeting(
            id="m",
            label="M",
            goal="g",
            roster=["alice"],
        )
        _apply_post_meeting_transitions(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[_feature_utterance("alpha")],
            current_item_slug="alpha",
        )
        assert get_state(tmp_path, "alpha") is None

    def test_transition_records_actor_and_notes(
        self, tmp_path: Path
    ) -> None:
        """Transitions fired by the workflow include 'system' actor
        + descriptive notes for audit trail."""
        meeting = Meeting(
            id="composition",
            label="M2.5",
            goal="g",
            roster=["white_rabbit"],
            transition_emitted_to="proposed",
        )
        _apply_emission_transition_for_utterance(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            utterance=_feature_utterance("alpha"),
        )
        history = transitions_for(tmp_path, "alpha")
        assert len(history) == 1
        assert history[0].by == "system"
        assert "composition" in (history[0].notes or "")


class TestEmissionHookFiresInEventLoop:
    """Regression: confirms the per-utterance hook actually fires
    inside _run_one_meeting's event loop, not just when called
    directly. The earlier obol2 design pass produced 5 features
    but feature-states.jsonl was never created — symptom of the
    hook silently no-opping in the real workflow path.

    The bug had two layers:
      1. v1 fix put the hook in _convene_one's event loop only;
         phased meetings (which M2 uses, since it has phases:
         [discussion, commit]) route through run_phased_meeting
         instead, bypassing the hook entirely.
      2. v2 fix mirrors the hook into the phased dispatch path.

    Both paths must be tested — the convene-one path covers
    legacy unphased meetings; the phased path covers the actual
    M2/M4 use cases in tdd-design.
    """

    async def test_run_one_meeting_writes_state_per_emission(
        self, tmp_path: Path
    ) -> None:
        from typing import AsyncIterator
        from wonderland.workflow import Workflow, _run_one_meeting

        # FakeRunner with project_root + a script that emits two
        # feature utterances then completes. Mirrors what M2 does
        # in a real run.
        from tests.test_workflow import FakeEvent, FakeRunner, FakeTelemetry

        class RunnerWithRoot(FakeRunner):
            def __init__(self, scripts, project_root):
                super().__init__(scripts)
                self.project_root = project_root

        meeting = Meeting(
            id="composition",
            label="M2",
            goal="ship features",
            roster=["white_rabbit"],
            meeting_budget=1.00,
            transition_emitted_to="proposed",
        )
        script = [
            FakeEvent(
                "utterance",
                {"utterance": _feature_utterance("alpha")},
            ),
            FakeEvent(
                "utterance",
                {"utterance": _feature_utterance("bravo")},
            ),
            FakeEvent(
                "complete",
                {"thread_id": "composition", "reason": "all done"},
            ),
        ]
        runner = RunnerWithRoot(
            {"composition": script}, project_root=tmp_path
        )

        from wonderland.workflow import WorkflowCapture

        capture = WorkflowCapture()
        async for _event in _run_one_meeting(
            meeting=meeting,
            runner=runner,
            capture=capture,
            directive=None,
            per_item_meetings={},
            current_item_kind=None,
            current_item_slug=None,
            thread_id="composition",
            iteration_index=None,
            iteration_total=None,
            iteration_label=None,
        ):
            pass

        # Both features should be at PROPOSED via transition_emitted_to
        # firing per-utterance.
        assert get_state(tmp_path, "alpha") == FeatureState.PROPOSED, (
            "transition_emitted_to didn't fire for alpha — "
            "per-utterance hook isn't reaching the event loop"
        )
        assert get_state(tmp_path, "bravo") == FeatureState.PROPOSED

    async def test_phased_meeting_writes_state_per_emission(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Phased meetings (meeting.phases is non-empty) route through
        run_phased_meeting, which bypasses _convene_one's event loop.
        The per-utterance hook must fire on this path too.

        Regression: obol2's M2 has phases [discussion, commit] and
        emitted 5 features; feature-states.jsonl was never written
        because the hook was only wired into the legacy convene
        path. M3's iterate_only_in_states: [proposed] then filtered
        all 5 features out (no state record → no match), and M3
        skipped entirely.
        """
        from typing import AsyncIterator, Any
        from wonderland.workflow import (
            PhaseSpec,
            WorkflowCapture,
            _run_one_meeting,
        )
        import wonderland.workflow as workflow_module

        # Stub out run_phased_meeting to yield two utterance events
        # without actually running an LLM. This isolates the hook
        # wiring at the workflow.py dispatch level — the only thing
        # we're testing is whether _run_one_meeting's phased branch
        # forwards utterance events through the lifecycle hook.
        async def fake_run_phased_meeting(*, meeting, **_kwargs) -> AsyncIterator[Any]:
            from wonderland.runner import RunnerEvent

            yield RunnerEvent(
                kind="utterance",
                elapsed=0.0,
                payload={"utterance": _feature_utterance("alpha")},
            )
            yield RunnerEvent(
                kind="utterance",
                elapsed=0.0,
                payload={"utterance": _feature_utterance("bravo")},
            )

        # Patch the import that workflow.py does inline. The phased
        # branch in _run_one_meeting does
        # ``from wonderland.meeting import run_phased_meeting`` at
        # call time, so patching the wonderland.meeting module is
        # what intercepts.
        import wonderland.meeting as meeting_module

        monkeypatch.setattr(
            meeting_module, "run_phased_meeting", fake_run_phased_meeting
        )

        meeting = Meeting(
            id="composition",
            label="M2",
            goal="ship features",
            roster=["white_rabbit"],
            meeting_budget=1.00,
            transition_emitted_to="proposed",
            phases=[
                PhaseSpec(name="discussion", max_rotations=3),
                PhaseSpec(name="commit", max_rotations=2),
            ],
        )

        # Minimal runner stub — phased path needs project_root for
        # the phase_event_writer plus the lifecycle hook.
        from tests.test_workflow import FakeRunner

        class RunnerWithRoot(FakeRunner):
            def __init__(self, project_root):
                super().__init__({})
                self.project_root = project_root

        runner = RunnerWithRoot(project_root=tmp_path)
        # phase_event_writer writes to .wonderland/phase-events.jsonl
        (tmp_path / ".wonderland").mkdir(exist_ok=True)

        capture = WorkflowCapture()
        async for _event in _run_one_meeting(
            meeting=meeting,
            runner=runner,
            capture=capture,
            directive=None,
            per_item_meetings={},
            current_item_kind=None,
            current_item_slug=None,
            thread_id="composition",
            iteration_index=None,
            iteration_total=None,
            iteration_label=None,
        ):
            pass

        assert get_state(tmp_path, "alpha") == FeatureState.PROPOSED, (
            "phased path didn't fire transition_emitted_to — "
            "this is the obol2 M3-skip bug"
        )
        assert get_state(tmp_path, "bravo") == FeatureState.PROPOSED

    async def test_phased_meeting_fires_transition_iteration_to(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """transition_iteration_to fires on phased COMPLETE just like
        the convene-one path. Without this, M3's transition_iteration_to:
        in_design never fires for phased meetings → features stuck at
        proposed → M5's iterate_only_in_states: [in_design] filters
        them all out → M5 skips with "(no items)".

        Same shape as the transition_emitted_to bug, one layer down
        the lifecycle. Caught from obol2's run after M3 finally
        worked: M5 reported zero iterations despite M3 having
        decomposed features.
        """
        from typing import AsyncIterator, Any
        from wonderland.workflow import (
            MeetingEndEvent,
            PhaseSpec,
            WorkflowCapture,
            _run_one_meeting,
        )

        # Pre-seed: alpha at proposed (M2 already shipped it).
        # M3-style meeting iterating on alpha should transition it
        # to in_design on COMPLETE.
        transition(tmp_path, "alpha", FeatureState.PROPOSED, by="rabbit")

        async def fake_run_phased_meeting(*, meeting, **_kwargs) -> AsyncIterator[Any]:
            # No utterances emitted — M3 doesn't emit features, it
            # decomposes the iteration item via tickets. Just yield
            # MeetingEndEvent with COMPLETE outcome to trigger the
            # transition_iteration_to path.
            yield MeetingEndEvent(
                meeting=meeting,
                outcome="COMPLETE",
                elapsed_s=0.0,
                calls_delta=0,
                cost_delta=0.0,
                artifact_kinds={},
                thread_id="decomposition-alpha",
                iteration_index=1,
                iteration_total=1,
                iteration_label="alpha",
            )

        import wonderland.meeting as meeting_module

        monkeypatch.setattr(
            meeting_module, "run_phased_meeting", fake_run_phased_meeting
        )

        meeting = Meeting(
            id="decomposition",
            label="M3",
            goal="decompose into tickets",
            roster=["white_rabbit"],
            per_item="feature",
            transition_iteration_to="in_design",
            phases=[PhaseSpec(name="decompose", max_rotations=3)],
        )

        from tests.test_workflow import FakeRunner

        class RunnerWithRoot(FakeRunner):
            def __init__(self, project_root):
                super().__init__({})
                self.project_root = project_root

        runner = RunnerWithRoot(project_root=tmp_path)
        (tmp_path / ".wonderland").mkdir(exist_ok=True)

        capture = WorkflowCapture()
        async for _event in _run_one_meeting(
            meeting=meeting,
            runner=runner,
            capture=capture,
            directive=None,
            per_item_meetings={},
            current_item_kind="feature",
            current_item_slug="alpha",
            thread_id="decomposition-alpha",
            iteration_index=1,
            iteration_total=1,
            iteration_label="alpha",
        ):
            pass

        assert get_state(tmp_path, "alpha") == FeatureState.IN_DESIGN, (
            "phased path didn't fire transition_iteration_to — "
            "this is the obol2 M5-skip bug"
        )


# --- T86 input filter integration via Meeting model ---


class TestInputFilterFieldShape:
    """The actual filter integration with per_item iteration is
    exercised in the broader workflow tests (FakeRunner doesn't have
    project_root set so the filter no-ops in those tests, which is
    the right back-compat behavior). These tests cover the field
    shape + that the filter passes through Meeting validation."""

    def test_filter_with_single_state(self) -> None:
        m = Meeting(
            id="implementation",
            label="M5",
            goal="ship",
            roster=["tweedledee"],
            per_item="ticket",
            iterate_only_in_states=["queued"],
        )
        assert m.iterate_only_in_states == ["queued"]

    def test_filter_with_multiple_states(self) -> None:
        m = Meeting(
            id="reopen",
            label="M-reopen",
            goal="re-engage",
            roster=["caterpillar"],
            per_item="feature",
            iterate_only_in_states=["queued", "in_progress"],
        )
        assert m.iterate_only_in_states == ["queued", "in_progress"]

    def test_filter_serializes_via_yaml(self) -> None:
        """Round-trip via Pydantic dump → validate confirms the
        field carries through workflow YAML parsing."""
        m = Meeting(
            id="implementation",
            label="M5",
            goal="ship",
            roster=["tweedledee"],
            per_item="ticket",
            iterate_only_in_states=["queued"],
        )
        roundtripped = Meeting.model_validate(m.model_dump())
        assert roundtripped.iterate_only_in_states == ["queued"]


# --- per_item items collection: cross-workflow disk fallback (the
# fix that made tdd-implement actually iterate on prior-workflow
# tickets/features) ---


class TestPerItemDiskFallback:
    """The per_item items collection now falls back to disk when the
    bus has no matching artifacts. Without this, tdd-implement's M6
    (per_item: ticket) hits the synthetic-skip path and completes
    empty because tickets came from tdd-design's M3 (a different
    workflow run, so utterances aren't on this run's bus)."""

    def test_per_item_items_from_disk_when_bus_empty(
        self, tmp_path: Path
    ) -> None:
        """When the bus has no ticket artifacts but the project has
        tickets on disk, per_item iteration should pick them up."""
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import _run_one_meeting  # noqa: F401

        # Drop a ticket on disk
        TicketRegistry(tmp_path).write(TicketPayload(
            title="Build account API",
            owner="tweedledum",
            tier="v1",
            estimate="2 days",
            description="Backend endpoint",
            sources=["see-money"],
        ))
        # Verify disk-fallback returns the ticket as a synthetic
        # utterance with the right slug + payload shape (which is
        # what the per_item items collection consumes)
        from wonderland.seeds_fallback import disk_seeds_for_kinds

        synthetic = disk_seeds_for_kinds(
            tmp_path, ["ticket"], thread_id="implementation"
        )
        assert len(synthetic) == 1
        artifact = synthetic[0].content.artifacts[0]
        assert artifact.kind == "ticket"
        assert artifact.payload["slug"] == "build-account-api"
        assert artifact.payload["title"] == "Build account API"


# --- _ticket_to_feature_map: ticket-side source-of-truth ---


class TestTicketToFeatureLookup:
    """The lookup uses ticket.sources (each ticket points at its
    parent feature) rather than feature.tickets (the feature lists
    its constituent tickets). This is more robust because:
      - M2 emits features BEFORE M3 produces tickets, so feature.
        tickets is invented at M2 time and may not match real
        slugs.
      - ticket.sources is naturally one-directional and tracks
        the actual decomposition that happened in M3.
    Per the M3 directive: each ticket's sources list MUST start
    with the parent feature's slug."""

    def test_lookup_uses_ticket_sources_field(
        self, tmp_path: Path
    ) -> None:
        """Tickets whose sources include a feature slug get linked
        to that feature in the lookup map."""
        from wonderland.feature import FeaturePayload, FeatureRegistry
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import _ticket_to_feature_map

        FeatureRegistry(tmp_path).write(FeaturePayload(
            title="Account dashboard",
            description="Balance at a glance.",
            tickets=["balance-card"],  # incorrect — slug doesn't exist
            stack_span="full-stack",
            tier="v1",
            sources=["see-money"],
        ))
        TicketRegistry(tmp_path).write(TicketPayload(
            title="Build balance API",
            owner="tweedledum",
            tier="v1",
            estimate="2 days",
            description="Backend API for balance",
            sources=["account-dashboard"],  # parent feature slug
        ))

        lookup = _ticket_to_feature_map(tmp_path)
        assert lookup == {"build-balance-api": "account-dashboard"}

    def test_lookup_takes_first_feature_slug_in_sources(
        self, tmp_path: Path
    ) -> None:
        """When a ticket lists multiple sources, the first one that
        matches a feature slug becomes the parent. Per M3 directive
        the parent feature is required to be FIRST."""
        from wonderland.feature import FeaturePayload, FeatureRegistry
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import _ticket_to_feature_map

        FeatureRegistry(tmp_path).write(FeaturePayload(
            title="Feature A",
            description="d", tickets=["t1"],
            stack_span="full-stack", tier="v1", sources=["s1"],
        ))
        FeatureRegistry(tmp_path).write(FeaturePayload(
            title="Feature B",
            description="d", tickets=["t2"],
            stack_span="full-stack", tier="v1", sources=["s2"],
        ))
        TicketRegistry(tmp_path).write(TicketPayload(
            title="Ticket",
            owner="tweedledum",
            tier="v1",
            estimate="1 day",
            description="x",
            sources=["feature-a", "feature-b", "story-x"],
        ))

        lookup = _ticket_to_feature_map(tmp_path)
        assert lookup == {"ticket": "feature-a"}

    def test_lookup_ignores_non_feature_sources(
        self, tmp_path: Path
    ) -> None:
        """Tickets whose sources are story slugs (not feature
        slugs) won't appear in the lookup. They're orphans for the
        purposes of the per_item: ticket iteration."""
        from wonderland.feature import FeaturePayload, FeatureRegistry
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import _ticket_to_feature_map

        FeatureRegistry(tmp_path).write(FeaturePayload(
            title="Feature A",
            description="d", tickets=["t1"],
            stack_span="full-stack", tier="v1", sources=["s1"],
        ))
        TicketRegistry(tmp_path).write(TicketPayload(
            title="Orphan ticket",
            owner="tweedledum",
            tier="v1",
            estimate="1 day",
            description="x",
            sources=["see-money", "user-auth"],  # all stories
        ))

        lookup = _ticket_to_feature_map(tmp_path)
        # Orphan ticket — not in lookup
        assert "orphan-ticket" not in lookup

    def test_lookup_empty_when_no_features(
        self, tmp_path: Path
    ) -> None:
        from wonderland.workflow import _ticket_to_feature_map

        assert _ticket_to_feature_map(tmp_path) == {}


# --- T93 parallel per_item iteration ---


class TestParallelPerItem:
    """T93: when meeting.parallel is True, per_item iterations run
    concurrently via stream-merge instead of sequentially. Tests
    the stream-merge helper directly + verify the Meeting field."""

    async def test_merge_async_iterators_yields_from_all(self) -> None:
        """Stream-merge yields events from every iterator, eventually."""
        import asyncio

        from wonderland.workflow import _merge_async_iterators

        async def _iter_a():
            yield "a1"
            await asyncio.sleep(0)  # let other tasks run
            yield "a2"

        async def _iter_b():
            yield "b1"
            await asyncio.sleep(0)
            yield "b2"

        events: list[str] = []
        async for event in _merge_async_iterators([_iter_a(), _iter_b()]):
            events.append(event)

        # All four events surface, regardless of interleaving.
        assert sorted(events) == ["a1", "a2", "b1", "b2"]

    async def test_merge_async_iterators_handles_empty_list(self) -> None:
        """Empty iterator list yields nothing without erroring."""
        from wonderland.workflow import _merge_async_iterators

        events: list = []
        async for event in _merge_async_iterators([]):
            events.append(event)
        assert events == []

    def test_meeting_parallel_field_default_false(self) -> None:
        """parallel defaults to False — back-compat for all existing
        per_item meetings."""
        m = Meeting(
            id="m",
            label="M",
            goal="g",
            roster=["alice"],
            per_item="feature",
        )
        assert m.parallel is False

    def test_meeting_parallel_field_set_true(self) -> None:
        m = Meeting(
            id="decomposition",
            label="M3",
            goal="g",
            roster=["white_rabbit"],
            per_item="feature",
            parallel=True,
        )
        assert m.parallel is True

    def test_tdd_design_m3_and_m5_are_parallel(self) -> None:
        """The bundled tdd-design workflow opts M3 + M5 into
        parallel iteration."""
        from wonderland.workflow import load_workflow

        wf = load_workflow("tdd-design")
        m3 = wf.meeting_by_id("decomposition")
        m5 = wf.meeting_by_id("contract-negotiation")
        assert m3 is not None and m3.parallel is True
        assert m5 is not None and m5.parallel is True

    def test_tdd_implement_meetings_are_not_parallel(self) -> None:
        """tdd-implement uses pipeline mode for parallelism, not
        meeting-level parallel iteration. Each meeting stays sequential
        WITHIN a lane (M6/M7 ticket-level work could race on src/);
        the pipeline block parallelizes the outer feature lanes. So
        no meeting should set parallel: true — that would double-
        parallelize and recreate the file-race risk pipeline mode
        is structured to avoid."""
        from wonderland.workflow import load_workflow

        wf = load_workflow("tdd-implement")
        for meeting in wf.meetings:
            assert meeting.parallel is False, (
                f"meeting {meeting.id} should not have parallel=True "
                f"in tdd-implement — pipeline mode handles cross-feature "
                f"parallelism; meeting-level parallel would double up"
            )

    def test_tdd_implement_uses_two_level_pipeline(self) -> None:
        """tdd-implement uses a two-level pipeline: outer feature
        (sequential) + inner ticket (parallel). Tickets within a
        feature flow M6→M7 in true pipeline; M8 runs once per
        feature after the ticket block. Regression-guards the YAML
        wiring."""
        from wonderland.workflow import load_workflow

        wf = load_workflow("tdd-implement")
        assert wf.pipeline is not None, (
            "tdd-implement must declare pipeline: — that's how the "
            "ticket-parallel-within-sequential-feature shape is "
            "expressed"
        )
        assert wf.pipeline.levels is not None
        assert len(wf.pipeline.levels) == 2, (
            "tdd-implement is two-level (feature → ticket); single-"
            "level shape was the pre-0.3.4 form"
        )

        # Outer level: feature, sequential, gated on queued/in_progress
        outer = wf.pipeline.levels[0]
        assert outer.per_item == "feature"
        assert outer.parallel is False, (
            "features run sequentially — operator-mental-model + "
            "src/ race avoidance"
        )
        assert outer.iterate_only_in_states == ["queued", "in_progress"]

        # Inner level: ticket, parallel
        inner = wf.pipeline.levels[1]
        assert inner.per_item == "ticket"
        assert inner.parallel is True, (
            "tickets within a feature run in true pipeline — that's "
            "the whole point of two-level"
        )
