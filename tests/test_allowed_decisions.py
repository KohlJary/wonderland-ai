"""Tests for the P15 T-m6 stage-leak guardrail.

The substrate filter sits on each WonderlandAgent's publish path.
When a meeting's thread has registered allowed_decisions, the agent
strips artifacts from utterances whose speech_act isn't on the list,
deletes the on-disk files those artifacts wrote, and (when wired)
emits an ArtifactSuppressed observer event.

These tests exercise the substrate piece directly without spinning
up the full meeting machinery — same shape as the interview-substrate
tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.utterance import (
    AgentIdentity,
    Artifact,
    SpeechAct,
    Utterance,
    UtteranceContent,
)
from wonderland.workflow import (
    Meeting,
    Workflow,
    clear_active_disallowed_decisions,
    clear_thread_allowed_decisions,
    get_active_disallowed_decisions,
    get_thread_allowed_decisions,
    set_active_disallowed_decisions,
    set_thread_allowed_decisions,
)


# --------------------------------------------------------------------- #
# Meeting.allowed_decisions field
# --------------------------------------------------------------------- #


def test_meeting_defaults_allowed_decisions_to_none() -> None:
    m = Meeting(id="t", label="M1", goal="g", roster=["alice"])
    assert m.allowed_decisions is None


def test_meeting_accepts_allowed_decisions_list() -> None:
    m = Meeting(
        id="t",
        label="M1",
        goal="g",
        roster=["alice"],
        allowed_decisions=["milestone_plan", "concern"],
    )
    assert m.allowed_decisions == ["milestone_plan", "concern"]


# --------------------------------------------------------------------- #
# Thread registry
# --------------------------------------------------------------------- #


def test_thread_registry_set_and_get() -> None:
    set_thread_allowed_decisions("t1", ["milestone_plan"])
    try:
        assert get_thread_allowed_decisions("t1") == frozenset(
            {"milestone_plan"}
        )
    finally:
        clear_thread_allowed_decisions("t1")


def test_thread_registry_returns_none_when_unset() -> None:
    assert get_thread_allowed_decisions("never-set") is None


def test_thread_registry_empty_list_clears_entry() -> None:
    """Passing an empty list (or None) clears the entry — preserves
    the no-filter default behavior."""
    set_thread_allowed_decisions("t1", ["milestone_plan"])
    set_thread_allowed_decisions("t1", [])
    assert get_thread_allowed_decisions("t1") is None


def test_thread_registry_none_clears_entry() -> None:
    set_thread_allowed_decisions("t1", ["milestone_plan"])
    set_thread_allowed_decisions("t1", None)
    assert get_thread_allowed_decisions("t1") is None


def test_thread_registry_clear_explicit() -> None:
    set_thread_allowed_decisions("t1", ["milestone_plan"])
    clear_thread_allowed_decisions("t1")
    assert get_thread_allowed_decisions("t1") is None


def test_thread_registry_independent_threads() -> None:
    """Concurrent meetings on distinct threads keep distinct
    filters."""
    set_thread_allowed_decisions("t1", ["milestone_plan"])
    set_thread_allowed_decisions("t2", ["story"])
    try:
        assert get_thread_allowed_decisions("t1") == frozenset(
            {"milestone_plan"}
        )
        assert get_thread_allowed_decisions("t2") == frozenset(
            {"story"}
        )
    finally:
        clear_thread_allowed_decisions("t1")
        clear_thread_allowed_decisions("t2")


# --------------------------------------------------------------------- #
# Agent filter — strips artifacts + deletes files when speech_act
# isn't allowed
# --------------------------------------------------------------------- #


@pytest.fixture
def fake_agent():
    """Minimal-construction harness for the filter tests. Doesn't
    inherit from WonderlandAgent (its constructor chain is heavy);
    instead reuses the filter methods via function-binding off the
    real class.

    We expose:
      - ``identity``: a tiny stub with a ``name`` attribute, used by
        ``_emit_suppressed_event`` to populate the event's agent
        field.
      - The three filter methods, lifted directly from WonderlandAgent.
    """

    class _IdentityStub:
        name = "test_agent"

    class _MinimalAgent:
        from wonderland.agent import WonderlandAgent as _WA

        identity = _IdentityStub()
        _apply_allowed_decisions_filter = (
            _WA._apply_allowed_decisions_filter
        )
        _delete_artifact_file = _WA._delete_artifact_file
        _emit_suppressed_event = _WA._emit_suppressed_event

    return _MinimalAgent()


def _utt(
    *,
    thread_id: str,
    speech_act: SpeechAct,
    artifacts: list[Artifact],
    body: str = "",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(
            name="test_agent", constitution_version="test"
        ),
        addressed_to="caucus",
        speech_act=speech_act,
        content=UtteranceContent(body=body, artifacts=artifacts),
    )


def test_filter_passes_through_when_no_thread_filter(fake_agent) -> None:
    """No allowed_decisions registered for the thread → utterance
    passes through unchanged (preserves all existing workflows'
    behavior)."""
    utt = _utt(
        thread_id="unrestricted",
        speech_act=SpeechAct.TICKET,
        artifacts=[
            Artifact(kind="ticket", payload={"path": "/tmp/x.md"})
        ],
    )
    out = fake_agent._apply_allowed_decisions_filter(utt)
    assert out is utt
    assert len(out.content.artifacts) == 1


def test_filter_passes_through_when_speech_act_allowed(
    fake_agent,
) -> None:
    """speech_act on the allowed list → no filtering."""
    set_thread_allowed_decisions(
        "t-allowed", ["milestone_plan", "concern"]
    )
    try:
        utt = _utt(
            thread_id="t-allowed",
            speech_act=SpeechAct.MILESTONE_PLAN,
            artifacts=[
                Artifact(
                    kind="milestone",
                    payload={"slug": "foundation"},
                )
            ],
        )
        out = fake_agent._apply_allowed_decisions_filter(utt)
        assert out is utt
        assert len(out.content.artifacts) == 1
    finally:
        clear_thread_allowed_decisions("t-allowed")


def test_filter_strips_artifacts_when_speech_act_not_allowed(
    fake_agent, tmp_path: Path
) -> None:
    """speech_act NOT on the allowed list → artifacts stripped from
    the utterance (the utterance itself stays as a transcript
    record)."""
    # Create an actual file the artifact points at so the filter
    # has something to delete.
    ticket_file = tmp_path / "ticket-001-leaked.md"
    ticket_file.write_text("# leaked\n", encoding="utf-8")

    set_thread_allowed_decisions(
        "t-restricted", ["milestone_plan", "concern"]
    )
    try:
        utt = _utt(
            thread_id="t-restricted",
            speech_act=SpeechAct.TICKET,
            artifacts=[
                Artifact(
                    kind="ticket",
                    payload={
                        "slug": "leaked",
                        "path": str(ticket_file),
                    },
                )
            ],
            body="here's a ticket",
        )
        out = fake_agent._apply_allowed_decisions_filter(utt)
        # Artifacts stripped
        assert out.content.artifacts == []
        # Body / speech_act preserved (utterance stays as transcript)
        assert out.content.body == "here's a ticket"
        assert out.speech_act is SpeechAct.TICKET
        # On-disk file deleted
        assert not ticket_file.exists()
    finally:
        clear_thread_allowed_decisions("t-restricted")


def test_filter_strips_all_artifacts_when_multiple_in_utterance(
    fake_agent, tmp_path: Path
) -> None:
    """An utterance with multiple disallowed artifacts gets all of
    them stripped, all of their on-disk files deleted."""
    file_a = tmp_path / "ticket-001-a.md"
    file_b = tmp_path / "ticket-002-b.md"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    set_thread_allowed_decisions("t-strict", ["milestone_plan"])
    try:
        utt = _utt(
            thread_id="t-strict",
            speech_act=SpeechAct.TICKET,
            artifacts=[
                Artifact(kind="ticket", payload={"path": str(file_a)}),
                Artifact(kind="ticket", payload={"path": str(file_b)}),
            ],
        )
        out = fake_agent._apply_allowed_decisions_filter(utt)
        assert out.content.artifacts == []
        assert not file_a.exists()
        assert not file_b.exists()
    finally:
        clear_thread_allowed_decisions("t-strict")


def test_filter_tolerates_missing_file(
    fake_agent, tmp_path: Path
) -> None:
    """If the artifact's path doesn't exist (already deleted /
    operator hand-deleted between agent ship + filter), the delete
    is best-effort and doesn't crash."""
    missing_path = tmp_path / "never-existed.md"
    set_thread_allowed_decisions("t-strict", ["milestone_plan"])
    try:
        utt = _utt(
            thread_id="t-strict",
            speech_act=SpeechAct.TICKET,
            artifacts=[
                Artifact(
                    kind="ticket",
                    payload={"path": str(missing_path)},
                )
            ],
        )
        out = fake_agent._apply_allowed_decisions_filter(utt)
        assert out.content.artifacts == []
    finally:
        clear_thread_allowed_decisions("t-strict")


def test_filter_tolerates_artifact_without_path(fake_agent) -> None:
    """Artifacts whose payload doesn't have a 'path' key (e.g.,
    operator_question_options) just get stripped — no file to
    delete, no error."""
    set_thread_allowed_decisions("t-strict", ["milestone_plan"])
    try:
        utt = _utt(
            thread_id="t-strict",
            speech_act=SpeechAct.QUESTION,
            artifacts=[
                Artifact(
                    kind="operator_question_options",
                    payload={"options": ["A", "B"]},
                )
            ],
        )
        out = fake_agent._apply_allowed_decisions_filter(utt)
        assert out.content.artifacts == []
    finally:
        clear_thread_allowed_decisions("t-strict")


def test_filter_skips_utterance_with_no_artifacts(fake_agent) -> None:
    """Pure-text utterances (concern, question, deference, silence)
    have no artifacts to filter — pass through unchanged regardless
    of speech_act / allowed list."""
    set_thread_allowed_decisions("t-strict", ["milestone_plan"])
    try:
        utt = _utt(
            thread_id="t-strict",
            speech_act=SpeechAct.CONCERN,
            artifacts=[],
            body="this is a concern",
        )
        out = fake_agent._apply_allowed_decisions_filter(utt)
        assert out is utt
        assert out.content.body == "this is a concern"
    finally:
        clear_thread_allowed_decisions("t-strict")


def test_filter_emits_suppressed_event_per_artifact(
    fake_agent, tmp_path: Path
) -> None:
    """When wired with a suppressed_artifact_handler, the filter
    emits one ArtifactSuppressed event per dropped artifact carrying
    the meeting's allowed-list as reason."""
    from wonderland.observer.events import ArtifactSuppressed

    file_a = tmp_path / "t-a.md"
    file_b = tmp_path / "t-b.md"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    events: list[ArtifactSuppressed] = []
    fake_agent._suppressed_artifact_handler = events.append

    set_thread_allowed_decisions("t-strict", ["milestone_plan"])
    try:
        utt = _utt(
            thread_id="t-strict",
            speech_act=SpeechAct.TICKET,
            artifacts=[
                Artifact(kind="ticket", payload={"path": str(file_a)}),
                Artifact(kind="ticket", payload={"path": str(file_b)}),
            ],
        )
        fake_agent._apply_allowed_decisions_filter(utt)
    finally:
        clear_thread_allowed_decisions("t-strict")

    assert len(events) == 2
    for ev in events:
        assert ev.thread_id == "t-strict"
        assert ev.speech_act == "ticket"
        assert ev.artifact_kind == "ticket"
        assert ev.agent == "test_agent"
        assert "milestone_plan" in ev.reason


# --------------------------------------------------------------------- #
# Workflow.disallowed_decisions — P15 follow-up
# --------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _clear_disallowed():
    clear_active_disallowed_decisions()
    yield
    clear_active_disallowed_decisions()


def test_workflow_disallowed_decisions_defaults_none() -> None:
    """Workflows without an explicit kill-list have field=None,
    which the substrate treats as empty/no-op."""
    w = Workflow.model_validate(
        {
            "name": "wf",
            "description": "x",
            "version": 1,
            "meetings": [
                {
                    "id": "m",
                    "label": "M",
                    "goal": "g",
                    "roster": ["alice"],
                    "convenor_directive": "d",
                }
            ],
        }
    )
    assert w.disallowed_decisions is None


def test_workflow_disallowed_decisions_round_trips() -> None:
    w = Workflow.model_validate(
        {
            "name": "wf",
            "description": "x",
            "version": 1,
            "disallowed_decisions": ["milestone_plan", "interview_review"],
            "meetings": [
                {
                    "id": "m",
                    "label": "M",
                    "goal": "g",
                    "roster": ["alice"],
                    "convenor_directive": "d",
                }
            ],
        }
    )
    assert w.disallowed_decisions == ["milestone_plan", "interview_review"]


def test_active_disallowed_set_and_clear() -> None:
    assert get_active_disallowed_decisions() == frozenset()
    set_active_disallowed_decisions(["milestone_plan"])
    assert get_active_disallowed_decisions() == frozenset({"milestone_plan"})
    clear_active_disallowed_decisions()
    assert get_active_disallowed_decisions() == frozenset()


def test_active_disallowed_set_none_clears() -> None:
    set_active_disallowed_decisions(["x"])
    set_active_disallowed_decisions(None)
    assert get_active_disallowed_decisions() == frozenset()


def test_filter_strips_when_speech_act_in_workflow_disallowed(
    fake_agent, tmp_path
) -> None:
    """Substrate guard: even when the meeting doesn't declare
    allowed_decisions, the workflow-level kill-list strips artifacts
    of forbidden speech_acts from the bus (a downstream no-op).
    Validates the P15 follow-up that blocks milestone_plan emissions
    during tdd-design.

    NB (0.12.1): the strip suppresses the artifact but does NOT delete
    the milestone FILE — a milestone_plan emission during tdd-design is
    typically a RE-AFFIRMATION of the committed plan, and deleting its
    files would wipe the real milestones (wwu 2026-06-19). Milestones
    are owned only by the snapshot + retraction. A non-milestone leak's
    file IS still deleted (see ...speech_act_not_allowed above)."""
    file_path = tmp_path / "milestone-99-leaked.md"
    file_path.write_text("leaked milestone body")
    set_active_disallowed_decisions(["milestone_plan"])
    try:
        utt = _utt(
            thread_id="t-wf",
            speech_act=SpeechAct.MILESTONE_PLAN,
            artifacts=[
                Artifact(
                    kind="milestone",
                    payload={"path": str(file_path), "slug": "leaked"},
                )
            ],
        )
        result = fake_agent._apply_allowed_decisions_filter(utt)
        assert result.content.artifacts == []
        # Stripped from the bus, but the milestone file is preserved.
        assert file_path.exists()
    finally:
        clear_active_disallowed_decisions()


def test_filter_passthrough_when_speech_act_not_in_workflow_disallowed(
    fake_agent,
) -> None:
    """When the speech_act ISN'T on the workflow kill-list, the
    filter is a no-op (assuming no meeting-level filter)."""
    set_active_disallowed_decisions(["interview_review"])
    try:
        utt = _utt(
            thread_id="t-wf",
            speech_act=SpeechAct.STORY,
            artifacts=[Artifact(kind="story", payload={})],
        )
        result = fake_agent._apply_allowed_decisions_filter(utt)
        assert len(result.content.artifacts) == 1
    finally:
        clear_active_disallowed_decisions()


# --------------------------------------------------------------------- #
# Milestone files are never deleted by the decision-filter
# (regression: wwu 2026-06-19, 0.12.1 — the P21 diagram meeting wiped
# the whole milestone plan when an agent re-emitted it while drawing it)
# --------------------------------------------------------------------- #


def test_milestone_file_survives_meeting_allowed_decisions_strip(
    fake_agent, tmp_path: Path
) -> None:
    """The diagram meeting allows only ``diagram``. When an agent
    re-emits the milestone_plan while drawing it, the artifact gets
    stripped from the bus — but the milestone FILE (the planning
    phase's committed plan) must survive. Milestones are owned solely
    by the snapshot + explicit retraction, never the decision-filter."""
    milestone_file = tmp_path / "milestone-001-foundation.md"
    milestone_file.write_text(
        "## Milestone 01: Foundation\n", encoding="utf-8"
    )

    set_thread_allowed_decisions("t-diagram", ["diagram"])
    try:
        utt = _utt(
            thread_id="t-diagram",
            speech_act=SpeechAct.MILESTONE_PLAN,
            artifacts=[
                Artifact(
                    kind="milestone",
                    payload={
                        "slug": "foundation",
                        "path": str(milestone_file),
                    },
                )
            ],
        )
        out = fake_agent._apply_allowed_decisions_filter(utt)
        # Artifact stripped from the bus (downstream no-op) ...
        assert out.content.artifacts == []
        # ... but the committed milestone file SURVIVES.
        assert milestone_file.exists()
    finally:
        clear_thread_allowed_decisions("t-diagram")
