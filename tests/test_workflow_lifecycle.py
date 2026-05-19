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
        from wonderland.story import StoryPayload, StoryRegistry
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import _run_one_meeting  # noqa: F401

        # Register the story this ticket cites so the phantom-citation
        # filter (post-93306e6) doesn't drop the ticket from the
        # seed pool. Pre-filter, this test used a placeholder slug
        # which silently produced a corrupted record; the filter now
        # rightly drops fully-unanchored records.
        StoryRegistry(tmp_path).write(StoryPayload(
            title="See money",
            persona="placeholder", situation="x",
            need="As placeholder I want y so z.",
            acceptance=["a"], tier="core",
            confusion_flags=["placeholder"],
        ))
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


# --- Review-verdict routing lifecycle gate (post-validation pilot fix) ---


class TestFeatureInImplementationStateGate:
    """The bug from projects/validation pilot: tdd-design's
    consolidation meeting (per_item=feature) emitted a review
    artifact with verdict=request-changes calling out duplicate
    decompositions. The substrate's _route_blocking_review fired,
    back-filled fresh tickets to in_progress, then marked them done,
    mid-design. The fix: gate review-verdict routing on feature
    lifecycle state — only fire when the feature is in queued /
    in_progress / ready_for_review (i.e. actually being implemented).
    Design-stage features (proposed / in_design / designed) skip the
    routing entirely."""

    def test_returns_false_when_no_state_record(self, tmp_path: Path) -> None:
        from wonderland.workflow import _feature_in_implementation_state

        # No feature-states.jsonl at all → no state → no routing.
        assert (
            _feature_in_implementation_state(tmp_path, "any-feature")
            is False
        )

    def test_returns_false_for_design_states(self, tmp_path: Path) -> None:
        """proposed, in_design, designed → not implementation. The
        canonical projects/validation bug was a design-state feature
        triggering implementation routing."""
        from wonderland.feature_lifecycle import back_fill_state
        from wonderland.workflow import _feature_in_implementation_state

        for state in (
            FeatureState.PROPOSED,
            FeatureState.IN_DESIGN,
            FeatureState.DESIGNED,
        ):
            slug = f"f-{state.value}"
            back_fill_state(tmp_path, slug, state, notes="seed")
            assert (
                _feature_in_implementation_state(tmp_path, slug) is False
            ), f"state {state.value} should NOT trigger routing"

    def test_returns_true_for_implementation_states(
        self, tmp_path: Path
    ) -> None:
        """queued, in_progress, ready_for_review → routing fires.
        These are the lifecycle states where Caterpillar's M8 review
        verdicts legitimately mean 'mark tickets done + synthesize
        follow-ups'."""
        from wonderland.feature_lifecycle import back_fill_state
        from wonderland.workflow import _feature_in_implementation_state

        for state in (
            FeatureState.QUEUED,
            FeatureState.IN_PROGRESS,
            FeatureState.READY_FOR_REVIEW,
        ):
            slug = f"f-{state.value}"
            back_fill_state(tmp_path, slug, state, notes="seed")
            assert (
                _feature_in_implementation_state(tmp_path, slug) is True
            ), f"state {state.value} should trigger routing"

    def test_returns_false_for_terminal_states(self, tmp_path: Path) -> None:
        """verified, rejected → past implementation, no routing."""
        from wonderland.feature_lifecycle import back_fill_state
        from wonderland.workflow import _feature_in_implementation_state

        for state in (FeatureState.VERIFIED, FeatureState.REJECTED):
            slug = f"f-{state.value}"
            back_fill_state(tmp_path, slug, state, notes="seed")
            assert (
                _feature_in_implementation_state(tmp_path, slug) is False
            )


def _ticket_utterance(
    slug: str, title: str, sources: list[str]
):
    """Synthesize a ticket-emitting utterance for the attribution
    helper to scan. Mirrors the shape Rabbit emits at M3."""
    from wonderland.utterance import (
        AgentIdentity,
        Artifact,
        SpeechAct,
        Utterance,
        UtteranceContent,
    )

    return Utterance(
        thread_id="decomposition",
        speaker=AgentIdentity(name="white_rabbit", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.TICKET,
        content=UtteranceContent(
            body=f"Ticket: {slug}",
            artifacts=[
                Artifact(
                    kind="ticket",
                    payload={
                        "slug": slug,
                        "title": title,
                        "sources": list(sources),
                    },
                ),
            ],
        ),
    )


class TestTicketSourceAttribution:
    """The validation3 pilot revealed Rabbit's M3 ticket emissions
    drift across iterations — early iterations cite the feature
    slug correctly; later ones cite invented ``story-*`` slugs
    that don't resolve. Dashboard attribution breaks silently. The
    substrate auto-injects the iteration's feature slug as the
    first source — substrate-enforced rather than directive-
    dependent."""

    def _setup_ticket_on_disk(
        self, tmp_path: Path, slug: str, sources: list[str]
    ) -> Path:
        """Write a minimal ticket markdown with a Sources line."""
        from wonderland.ticket import (
            TicketPayload,
            TicketRegistry,
            TicketStackSpan,
            TicketTier,
        )

        reg = TicketRegistry(tmp_path)
        record = reg.write(TicketPayload(
            title=slug,
            description="d",
            owner="tweedledee",
            tier=TicketTier.V1,
            stack_span=TicketStackSpan.BACKEND,
            estimate="1d",
            acceptance=["a"],
            sources=sources or ["seed-feature"],
        ))
        return record.path

    def test_no_op_when_meeting_not_per_item_feature(
        self, tmp_path: Path
    ) -> None:
        from wonderland.workflow import (
            Meeting,
            _attribute_ticket_sources_to_iteration_feature,
        )

        meeting = Meeting(
            id="m7", label="M7", goal="g",
            roster=["tweedledee"], per_item="ticket",
        )
        _attribute_ticket_sources_to_iteration_feature(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[
                _ticket_utterance("t1", "T1", ["something"]),
            ],
            current_item_slug="some-ticket-slug",
        )
        tickets_dir = tmp_path / ".wonderland" / "tickets"
        assert not tickets_dir.exists() or not any(
            tickets_dir.glob("ticket-*.md")
        )

    def test_no_op_when_no_current_item_slug(self, tmp_path: Path) -> None:
        from wonderland.workflow import (
            Meeting,
            _attribute_ticket_sources_to_iteration_feature,
        )

        meeting = Meeting(
            id="m3", label="M3", goal="g",
            roster=["white_rabbit"], per_item="feature",
        )
        _attribute_ticket_sources_to_iteration_feature(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[
                _ticket_utterance("t1", "T1", ["something"]),
            ],
            current_item_slug=None,
        )

    def test_injects_feature_slug_when_missing_from_sources(
        self, tmp_path: Path
    ) -> None:
        """The canonical validation3 case: ticket on disk cites
        only a phantom ``story-foo`` slug; the helper prepends the
        iteration's feature slug to both the bus payload and the
        on-disk Sources line."""
        from wonderland.workflow import (
            Meeting,
            _attribute_ticket_sources_to_iteration_feature,
        )

        path = self._setup_ticket_on_disk(
            tmp_path,
            slug="backend-user-registration",
            sources=["story-user-registration"],
        )
        utterance = _ticket_utterance(
            "backend-user-registration",
            "Backend user registration",
            ["story-user-registration"],
        )

        meeting = Meeting(
            id="decomposition", label="M3", goal="g",
            roster=["white_rabbit"], per_item="feature",
        )
        _attribute_ticket_sources_to_iteration_feature(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[utterance],
            current_item_slug="user-registration-and-login",
        )

        text = path.read_text(encoding="utf-8")
        sources_line = next(
            line for line in text.splitlines()
            if line.startswith("**Sources:**")
        )
        assert sources_line.startswith(
            "**Sources:** user-registration-and-login, "
        )
        assert "story-user-registration" in sources_line

        payload = utterance.content.artifacts[0].payload
        assert payload["sources"] == [
            "user-registration-and-login",
            "story-user-registration",
        ]

    def test_no_op_when_feature_slug_already_in_sources(
        self, tmp_path: Path
    ) -> None:
        from wonderland.workflow import (
            Meeting,
            _attribute_ticket_sources_to_iteration_feature,
        )

        path = self._setup_ticket_on_disk(
            tmp_path,
            slug="page-crud",
            sources=["create-and-manage-pages-with-url-slugs", "page-storage"],
        )
        original = path.read_text(encoding="utf-8")

        meeting = Meeting(
            id="decomposition", label="M3", goal="g",
            roster=["white_rabbit"], per_item="feature",
        )
        _attribute_ticket_sources_to_iteration_feature(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[
                _ticket_utterance(
                    "page-crud", "Page CRUD",
                    ["create-and-manage-pages-with-url-slugs", "page-storage"],
                ),
            ],
            current_item_slug="create-and-manage-pages-with-url-slugs",
        )
        assert path.read_text(encoding="utf-8") == original

    def test_handles_empty_sources_list(self, tmp_path: Path) -> None:
        """A ticket emitted with no sources gets the feature slug as
        its single source (edge case but covers it explicitly)."""
        from wonderland.workflow import (
            Meeting,
            _attribute_ticket_sources_to_iteration_feature,
        )

        utterance = _ticket_utterance("orphan-ticket", "Orphan", [])
        meeting = Meeting(
            id="decomposition", label="M3", goal="g",
            roster=["white_rabbit"], per_item="feature",
        )
        _attribute_ticket_sources_to_iteration_feature(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[utterance],
            current_item_slug="parent-feature",
        )
        assert utterance.content.artifacts[0].payload["sources"] == [
            "parent-feature"
        ]

    def test_thread_id_scopes_attribution_to_iteration(
        self, tmp_path: Path
    ) -> None:
        """The validation4 pilot's defining failure: M3 parallel
        iterations share the global capture-slice, so each
        iteration's new_utterances contained sibling iterations'
        tickets too. The function attributed every iteration's
        feature slug to every ticket on the slice — final state
        had every ticket citing every feature.

        Fix: thread_id parameter scopes new_utterances to the
        iteration's own thread. Tickets emitted on other threads
        are filtered out before attribution touches them."""
        from wonderland.workflow import (
            Meeting,
            _attribute_ticket_sources_to_iteration_feature,
        )

        # Seed two tickets, one per "iteration". Registry slugifies
        # titles → lowercase slugs; match the slug we'll look up.
        self._setup_ticket_on_disk(
            tmp_path, slug="ticket-from-iter-a",
            sources=["story-a"],
        )
        self._setup_ticket_on_disk(
            tmp_path, slug="ticket-from-iter-b",
            sources=["story-b"],
        )

        utt_a = _ticket_utterance(
            "ticket-from-iter-a", "T-A", ["story-a"],
        )
        utt_a = utt_a.model_copy(update={"thread_id": "decomposition-feature-a"})
        utt_b = _ticket_utterance(
            "ticket-from-iter-b", "T-B", ["story-b"],
        )
        utt_b = utt_b.model_copy(update={"thread_id": "decomposition-feature-b"})

        meeting = Meeting(
            id="decomposition", label="M3", goal="g",
            roster=["white_rabbit"], per_item="feature",
        )

        # Iteration A completes — scope to thread A. Should only
        # touch ticket-from-iter-a, leave ticket-from-iter-b alone.
        _attribute_ticket_sources_to_iteration_feature(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[utt_a, utt_b],  # global slice has both
            current_item_slug="feature-a",
            thread_id="decomposition-feature-a",
        )

        tickets_dir = tmp_path / ".wonderland" / "tickets"
        a_text = next(tickets_dir.glob("*ticket-from-iter-a.md")).read_text()
        b_text = next(tickets_dir.glob("*ticket-from-iter-b.md")).read_text()

        # A got the feature slug prepended.
        assert "feature-a, story-a" in a_text
        # B was left alone — no cross-iteration contamination.
        assert "feature-a" not in b_text
        assert "story-b" in b_text

    def test_skips_non_ticket_artifacts(self, tmp_path: Path) -> None:
        """Feature / ADR / contract-note artifacts on the same bus
        shouldn't be touched — only tickets get source-attribution."""
        from wonderland.workflow import (
            Meeting,
            _attribute_ticket_sources_to_iteration_feature,
        )

        feature_utterance = _feature_utterance("some-feature", "Some feature")
        meeting = Meeting(
            id="decomposition", label="M3", goal="g",
            roster=["white_rabbit"], per_item="feature",
        )
        _attribute_ticket_sources_to_iteration_feature(
            meeting=meeting,
            runner=_runner_with_root(tmp_path),
            new_utterances=[feature_utterance],
            current_item_slug="parent-feature",
        )
        payload = feature_utterance.content.artifacts[0].payload
        assert "sources" not in payload or payload.get("sources") == []


class TestMilestonePlanSnapshot:
    """T-g9 follow-up — snapshot semantics for milestone_plan.

    Validation5 pilot: agents converged from m3-routine-generation
    to m3-equipment-and-routine across rotations, but the original
    m3-routine-generation file stayed on disk because the substrate
    treated milestone_plan as additive. The fix: at meeting end,
    each speaker's most-recent milestone_plan defines their claim;
    files outside the union of claims get deleted.
    """

    def _milestone_utterance(
        self,
        speaker: str,
        slugs: list[str],
    ):
        from wonderland.utterance import (
            AgentIdentity,
            Artifact,
            SpeechAct,
            Utterance,
            UtteranceContent,
        )

        return Utterance(
            thread_id="planning",
            speaker=AgentIdentity(
                name=speaker, constitution_version="0.1"
            ),
            addressed_to="caucus",
            speech_act=SpeechAct.MILESTONE_PLAN,
            content=UtteranceContent(
                body="plan",
                artifacts=[
                    Artifact(kind="milestone", payload={"slug": s})
                    for s in slugs
                ],
            ),
        )

    def _seed_milestone_files(
        self, tmp_path: Path, slugs: list[str]
    ) -> None:
        ms_dir = tmp_path / ".wonderland" / "milestones"
        ms_dir.mkdir(parents=True, exist_ok=True)
        for i, slug in enumerate(slugs, start=1):
            (ms_dir / f"milestone-{i:02d}-{slug}.md").write_text(
                f"## Milestone {i:02d}: {slug}\n\n"
                f"**Slug:** {slug}\n"
                f"**Order:** {i}\n"
                f"**Deferred:** false\n"
                f"**Confidence:** operator_stated\n\n"
                "**Goal:**\n\nx\n",
                encoding="utf-8",
            )

    def test_deletes_milestone_dropped_by_sole_emitter(
        self, tmp_path: Path
    ) -> None:
        from wonderland.workflow import _apply_milestone_plan_snapshot

        self._seed_milestone_files(
            tmp_path, ["m1-foo", "m2-bar", "m3-old-name"]
        )
        # Single speaker emits twice; second emission drops m3-old.
        utterances = [
            self._milestone_utterance(
                "alice", ["m1-foo", "m2-bar", "m3-old-name"]
            ),
            self._milestone_utterance(
                "alice", ["m1-foo", "m2-bar", "m3-new-name"]
            ),
        ]
        # Seed the file for m3-new-name too (the agent's write path
        # would have created it; we're just testing the snapshot).
        self._seed_milestone_files(
            tmp_path, ["m1-foo", "m2-bar", "m3-new-name"]
        )
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=utterances,
        )
        assert "m3-old-name" in deleted
        assert "m3-new-name" not in deleted
        files = sorted(
            p.name for p in (tmp_path / ".wonderland" / "milestones").iterdir()
        )
        assert not any("m3-old-name" in f for f in files)
        assert any("m3-new-name" in f for f in files)

    def test_preserves_milestones_in_active_set(
        self, tmp_path: Path
    ) -> None:
        """When the union of speakers' latest claims includes a
        slug, it stays — even if an earlier emission dropped it
        but a later emission re-added it."""
        from wonderland.workflow import _apply_milestone_plan_snapshot

        self._seed_milestone_files(
            tmp_path, ["m1-foo", "m2-bar"]
        )
        utterances = [
            self._milestone_utterance("alice", ["m1-foo"]),
            self._milestone_utterance("alice", ["m1-foo", "m2-bar"]),
        ]
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=utterances,
        )
        assert deleted == []

    def test_union_across_speakers_protects_claimed_milestones(
        self, tmp_path: Path
    ) -> None:
        """alice's plan has m1+m2; rabbit's plan has m3. Union is
        {m1, m2, m3}; nothing gets deleted. Multi-agent collaboration
        preserves each agent's last-stated claims."""
        from wonderland.workflow import _apply_milestone_plan_snapshot

        self._seed_milestone_files(tmp_path, ["m1-foo", "m2-bar", "m3-baz"])
        utterances = [
            self._milestone_utterance("alice", ["m1-foo", "m2-bar"]),
            self._milestone_utterance("white_rabbit", ["m3-baz"]),
        ]
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=utterances,
        )
        assert deleted == []

    def test_validation5_two_m3_consolidation_pattern(
        self, tmp_path: Path
    ) -> None:
        """The exact validation5 case: two agents converge from one
        M3 slug to a different M3 slug across rotations. The
        abandoned slug gets deleted; the new slug survives."""
        from wonderland.workflow import _apply_milestone_plan_snapshot

        self._seed_milestone_files(
            tmp_path,
            [
                "m1-marcus-logs-his-first-session",
                "m2-marcus-feels-progress-unfold",
                "m3-routine-generation-from-equipment",
                "m3-equipment-and-routine-generation",
            ],
        )
        utterances = [
            self._milestone_utterance(
                "alice",
                [
                    "m1-marcus-logs-his-first-session",
                    "m2-marcus-feels-progress-unfold",
                    "m3-routine-generation-from-equipment",
                ],
            ),
            self._milestone_utterance(
                "white_rabbit",
                [
                    "m1-marcus-logs-his-first-session",
                    "m2-marcus-feels-progress-unfold",
                    "m3-routine-generation-from-equipment",
                    "m3-equipment-and-routine-generation",
                ],
            ),
            self._milestone_utterance(
                "alice",
                [
                    "m1-marcus-logs-his-first-session",
                    "m2-marcus-feels-progress-unfold",
                    "m3-equipment-and-routine-generation",
                ],
            ),
            self._milestone_utterance(
                "white_rabbit",
                [
                    "m1-marcus-logs-his-first-session",
                    "m2-marcus-feels-progress-unfold",
                    "m3-equipment-and-routine-generation",
                ],
            ),
        ]
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=utterances,
        )
        assert deleted == ["m3-routine-generation-from-equipment"]

    def test_no_op_when_no_milestone_plan_utterances(
        self, tmp_path: Path
    ) -> None:
        from wonderland.workflow import _apply_milestone_plan_snapshot

        self._seed_milestone_files(tmp_path, ["m1-foo"])
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=[],
        )
        assert deleted == []
        # m1-foo should still be on disk.
        files = list(
            (tmp_path / ".wonderland" / "milestones").iterdir()
        )
        assert len(files) == 1

    def test_primary_speaker_filters_to_one_authors_claims(
        self, tmp_path: Path
    ) -> None:
        """Mvp-demo repro: Alice's persona-anchored track and
        Rabbit's technical track both survived the default snapshot
        (parallel slugs at same orders). With primary_speaker set
        to white_rabbit, only Rabbit's claims define the active
        set; Alice's milestones get snapshot-cleaned."""
        from wonderland.workflow import _apply_milestone_plan_snapshot

        # 5 alice milestones + 4 rabbit milestones, same orders 2-5.
        self._seed_milestone_files(
            tmp_path,
            [
                "m1-alice-foundation",
                "m2-alice-discovery",
                "m3-alice-edits",
                "m4-alice-rendering",
                "m5-alice-launch",
                "m2-rabbit-persistence",
                "m3-rabbit-api-surface",
                "m4-rabbit-frontend",
                "m5-rabbit-demo-shell",
            ],
        )
        utterances = [
            self._milestone_utterance(
                "alice",
                [
                    "m1-alice-foundation",
                    "m2-alice-discovery",
                    "m3-alice-edits",
                    "m4-alice-rendering",
                    "m5-alice-launch",
                ],
            ),
            self._milestone_utterance(
                "white_rabbit",
                [
                    "m2-rabbit-persistence",
                    "m3-rabbit-api-surface",
                    "m4-rabbit-frontend",
                    "m5-rabbit-demo-shell",
                ],
            ),
        ]
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=utterances,
            primary_speaker="white_rabbit",
        )
        # All 5 of Alice's milestones get cleaned; Rabbit's 4 survive.
        assert sorted(deleted) == sorted(
            [
                "m1-alice-foundation",
                "m2-alice-discovery",
                "m3-alice-edits",
                "m4-alice-rendering",
                "m5-alice-launch",
            ]
        )

    def test_primary_speaker_unset_uses_union_default(
        self, tmp_path: Path
    ) -> None:
        """When primary_speaker is None (default), the original
        union-of-authors-claims semantic applies — both speakers'
        milestones survive."""
        from wonderland.workflow import _apply_milestone_plan_snapshot

        self._seed_milestone_files(
            tmp_path, ["m1-alice-foundation", "m1-rabbit-bootstrap"]
        )
        utterances = [
            self._milestone_utterance(
                "alice", ["m1-alice-foundation"]
            ),
            self._milestone_utterance(
                "white_rabbit", ["m1-rabbit-bootstrap"]
            ),
        ]
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=utterances,
            # primary_speaker omitted (None)
        )
        # Both survive — union semantic.
        assert deleted == []

    def test_primary_speaker_no_emission_is_no_op(
        self, tmp_path: Path
    ) -> None:
        """When primary_speaker is set but the designated speaker
        didn't emit any milestone_plan utterances, the snapshot
        no-ops rather than deleting all on-disk milestones. Leaves
        operator able to re-run with the primary actually engaging."""
        from wonderland.workflow import _apply_milestone_plan_snapshot

        self._seed_milestone_files(
            tmp_path, ["m1-alice-foundation"]
        )
        utterances = [
            self._milestone_utterance(
                "alice", ["m1-alice-foundation"]
            ),
            # white_rabbit didn't emit milestone_plan.
        ]
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=utterances,
            primary_speaker="white_rabbit",
        )
        assert deleted == []

    def test_empty_emission_is_no_op_no_deletions(
        self, tmp_path: Path
    ) -> None:
        """Mvp-demo regression: Rabbit emitted ``milestone_plan``
        with an empty artifacts list during tdd-design M2 (he meant
        to re-emit m1 with an expanded done_when but shipped no
        artifact). The snapshot interpreted the empty list as
        ``active = {}`` and started unlinking files.

        Empty-active should no-op — abandonment is what the explicit
        ``retract`` decision mode is for.
        """
        from wonderland.workflow import _apply_milestone_plan_snapshot

        self._seed_milestone_files(
            tmp_path, ["m1-foundation", "m2-feature"]
        )
        utterances = [
            self._milestone_utterance("white_rabbit", []),
        ]
        deleted = _apply_milestone_plan_snapshot(
            runner=_runner_with_root(tmp_path),
            new_utterances=utterances,
        )
        assert deleted == []
        files = sorted(
            (tmp_path / ".wonderland" / "milestones").iterdir()
        )
        assert len(files) == 2


class TestRetractScopeGuard:
    """Validation5 follow-up: ticket retract is scoped to the current
    iteration. Out-of-scope retracts get rejected so an agent in
    iteration A can't accidentally delete artifacts owned by
    iteration B.
    """

    def _seed_ticket(
        self,
        tmp_path: Path,
        slug: str,
        sources: list[str],
    ) -> Path:
        tickets_dir = tmp_path / ".wonderland" / "tickets"
        tickets_dir.mkdir(parents=True, exist_ok=True)
        path = tickets_dir / f"ticket-01ABCDEF-{slug}.md"
        path.write_text(
            f"## Ticket 001: {slug}\n\n"
            f"**GUID:** 01ABCDEFGHJKMNPQRSTVWXYZ12\n"
            f"**Slug:** {slug}\n"
            f"**Sources:** {', '.join(sources)}\n"
            f"**Owner:** white_rabbit\n"
            f"**Tier:** v1\n"
            f"**Estimate:** 0.5d\n\n"
            f"**Description:**\n\nx\n",
            encoding="utf-8",
        )
        return path

    def _retract_utterance(
        self,
        speaker: str,
        thread_id: str,
        target_slug: str,
    ):
        from wonderland.utterance import (
            AgentIdentity,
            Artifact,
            SpeechAct,
            Utterance,
            UtteranceContent,
        )

        return Utterance(
            thread_id=thread_id,
            speaker=AgentIdentity(
                name=speaker, constitution_version="0.1"
            ),
            addressed_to="caucus",
            speech_act=SpeechAct.RETRACT,
            content=UtteranceContent(
                body="",
                artifacts=[
                    Artifact(
                        kind="retraction",
                        payload={
                            "target_kind": "ticket",
                            "target_slug": target_slug,
                            "reason": "out of scope",
                        },
                    )
                ],
            ),
        )

    def test_rejects_retract_when_ticket_sources_omit_iteration(
        self, tmp_path: Path
    ) -> None:
        """Validation5 repro: Caterpillar in iteration `feature-a`
        tries to retract a ticket whose sources point to `feature-b`.
        Substrate refuses; ticket file stays on disk."""
        from wonderland.workflow import _apply_retraction_for_utterance

        path = self._seed_ticket(
            tmp_path,
            slug="t-belongs-to-b",
            sources=["feature-b"],
        )
        utt = self._retract_utterance(
            speaker="caterpillar",
            thread_id="consolidation-feature-a",
            target_slug="t-belongs-to-b",
        )
        records = _apply_retraction_for_utterance(
            runner=_runner_with_root(tmp_path),
            utterance=utt,
            current_item_slug="feature-a",
        )
        assert records == []
        assert path.is_file()

    def test_allows_retract_when_ticket_sources_include_iteration(
        self, tmp_path: Path
    ) -> None:
        """In-scope retract still works: Caterpillar can clean up a
        ticket that legitimately belongs to his iteration."""
        from wonderland.workflow import _apply_retraction_for_utterance

        path = self._seed_ticket(
            tmp_path,
            slug="t-belongs-to-a",
            sources=["feature-a"],
        )
        utt = self._retract_utterance(
            speaker="caterpillar",
            thread_id="consolidation-feature-a",
            target_slug="t-belongs-to-a",
        )
        records = _apply_retraction_for_utterance(
            runner=_runner_with_root(tmp_path),
            utterance=utt,
            current_item_slug="feature-a",
        )
        assert len(records) == 1
        assert not path.exists()

    def test_no_scope_means_no_guard(self, tmp_path: Path) -> None:
        """When current_item_slug is None (non-per_item meetings),
        retract works unscoped — back-compat for milestone-plan
        and other non-iterated meetings."""
        from wonderland.workflow import _apply_retraction_for_utterance

        path = self._seed_ticket(
            tmp_path,
            slug="t-anywhere",
            sources=["whatever"],
        )
        utt = self._retract_utterance(
            speaker="caterpillar",
            thread_id="planning",
            target_slug="t-anywhere",
        )
        records = _apply_retraction_for_utterance(
            runner=_runner_with_root(tmp_path),
            utterance=utt,
            current_item_slug=None,
        )
        assert len(records) == 1
        assert not path.exists()

    def test_resolves_guid_prefixed_source_citation(
        self, tmp_path: Path
    ) -> None:
        """T-g5 guid:slug citations resolve correctly during scope
        check. Ticket sourced to ``feature-guid:feature-a`` passes
        scope when current_item_slug is ``feature-a``."""
        from wonderland.workflow import _apply_retraction_for_utterance

        path = self._seed_ticket(
            tmp_path,
            slug="t-guid-source",
            sources=["01ABCDEFGHJKMNPQRSTVWXYZ99:feature-a"],
        )
        utt = self._retract_utterance(
            speaker="caterpillar",
            thread_id="consolidation-feature-a",
            target_slug="t-guid-source",
        )
        records = _apply_retraction_for_utterance(
            runner=_runner_with_root(tmp_path),
            utterance=utt,
            current_item_slug="feature-a",
        )
        assert len(records) == 1
        assert not path.exists()


class TestSourceResolves:
    """T-g5 — source citation resolves to guid, slug, or guid:slug."""

    def test_resolves_legacy_slug_citation(self) -> None:
        from wonderland.workflow import _source_resolves

        slugs = {"my-story"}
        guids: set[str] = set()
        assert _source_resolves("my-story", slugs, guids) is True

    def test_resolves_full_guid_citation(self) -> None:
        from wonderland.workflow import _source_resolves

        guid = "01H8AB12CD34EF56GH78JK90MN"  # 26-char ULID-shaped
        slugs: set[str] = set()
        guids = {guid}
        assert _source_resolves(guid, slugs, guids) is True

    def test_resolves_guid_colon_slug_citation(self) -> None:
        from wonderland.workflow import _source_resolves

        guid = "01H8AB12CD34EF56GH78JK90MN"
        slugs = {"my-story"}
        guids = {guid}
        assert _source_resolves(f"{guid}:my-story", slugs, guids) is True

    def test_rejects_phantom_guid(self) -> None:
        from wonderland.workflow import _source_resolves

        slugs: set[str] = set()
        guids: set[str] = set()
        assert (
            _source_resolves(
                "01H8AB12CD34EF56GH78JK90MN", slugs, guids
            )
            is False
        )

    def test_rejects_phantom_slug(self) -> None:
        from wonderland.workflow import _source_resolves

        slugs = {"real-slug"}
        guids: set[str] = set()
        assert _source_resolves("phantom-slug", slugs, guids) is False

    def test_falls_back_to_slug_tail_when_guid_unresolved(self) -> None:
        """When guid prefix doesn't resolve but slug tail does — the
        operator may have hand-edited a file's guid, so accept the
        slug as evidence the citation is still meaningful."""
        from wonderland.workflow import _source_resolves

        slugs = {"my-story"}
        guids: set[str] = set()
        # Guid is invented; slug tail resolves.
        assert (
            _source_resolves(
                "01PHANTOMPHANTOMPHANTOMPHA:my-story", slugs, guids
            )
            is True
        )

    def test_rejects_empty_source(self) -> None:
        from wonderland.workflow import _source_resolves

        assert _source_resolves("", set(), set()) is False
