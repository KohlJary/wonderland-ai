"""Round-trip tests for ``observer.event_codec``. Each known
RunEvent type → to_jsonl → from_jsonl → equality. The codec is the
wire format for detached background runs (subprocess writes JSONL,
TUI reads it back), so a regression here corrupts the live-watch
view of any background run."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from wonderland.observer.event_codec import (
    UnknownEventKind,
    from_jsonl,
    to_jsonl,
)
from wonderland.observer.events import (
    AgentActed,
    AgentPassed,
    AgentTelemetryDelta,
    ArtifactShipped,
    MeetingEnded,
    MeetingStarted,
    PhaseEnded,
    PhaseStarted,
    PriorityWindowOpened,
    RotationCompleted,
    RunEnded,
    RunStarted,
    UtteranceEmitted,
)
from wonderland.observer.interface import (
    AgentTelemetry,
    RunArtifact,
    RunMeeting,
    RunSummary,
)
from wonderland.utterance import (
    AgentIdentity,
    SpeechAct,
    Utterance,
    UtteranceContent,
)


T0 = datetime(2026, 5, 10, 14, 0, 0, tzinfo=timezone.utc)


def _summary() -> RunSummary:
    return RunSummary(
        run_id="20260510T140000",
        workflow_name="tdd-design",
        directive="ship the thing",
        project_root=Path("/tmp/proj"),
        started_at=T0,
        ended_at=None,
        total_cost=0.42,
        total_calls=12,
        outcome=None,
    )


def _meeting() -> RunMeeting:
    return RunMeeting(
        id="m1",
        label="M1",
        name="Caucus Race",
        started_at=T0,
        ended_at=None,
        outcome=None,
        elapsed_seconds=None,
        calls=0,
        cost=0.0,
    )


def _utterance() -> Utterance:
    return Utterance(
        speaker=AgentIdentity(name="alice", constitution_version="v1"),
        addressed_to="caucus",
        speech_act=SpeechAct.OBSERVATION,
        content=UtteranceContent(body="hello"),
        thread_id="m1",
        timestamp=T0,
    )


def test_roundtrip_run_started() -> None:
    event = RunStarted(timestamp=T0, summary=_summary())
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_meeting_started() -> None:
    event = MeetingStarted(
        timestamp=T0,
        meeting=_meeting(),
        thread_id="m1",
        iteration_index=2,
        iteration_total=5,
        iteration_label="Break Timer",
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_utterance_emitted() -> None:
    event = UtteranceEmitted(timestamp=T0, utterance=_utterance())
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_artifact_shipped() -> None:
    artifact = RunArtifact(
        kind="story",
        path=Path("/tmp/proj/.wonderland/stories/foo.md"),
        title="Foo",
        created_at=T0,
    )
    event = ArtifactShipped(timestamp=T0, artifact=artifact)
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_agent_telemetry_delta() -> None:
    event = AgentTelemetryDelta(
        timestamp=T0,
        telemetry=AgentTelemetry(name="alice", calls=10, cost=0.30),
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_meeting_ended() -> None:
    event = MeetingEnded(
        timestamp=T0,
        meeting=_meeting(),
        thread_id="m1",
        outcome="COMPLETE",
        elapsed_seconds=42.5,
        calls_delta=12,
        cost_delta=0.50,
        artifact_kinds={"story": 3, "adr": 1},
        iteration_index=None,
        iteration_total=None,
        iteration_label=None,
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_run_ended() -> None:
    event = RunEnded(timestamp=T0, summary=_summary())
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_phase_started_with_tuple_cast() -> None:
    """The ``cast`` field is a tuple — JSON can't preserve that; the
    decoder coerces lists back to tuple based on the field type."""
    event = PhaseStarted(
        timestamp=T0,
        meeting_thread_id="m4",
        phase_name="red",
        max_rotations=3,
        cast=("alice", "hatter"),
        exit_condition_artifact=None,
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event
    assert isinstance(decoded.cast, tuple)


def test_roundtrip_phase_ended() -> None:
    event = PhaseEnded(
        timestamp=T0,
        meeting_thread_id="m4",
        phase_name="red",
        reason="succession",
        rotations_used=2,
        total_windows=6,
        passes_per_agent={"alice": 2, "hatter": 1},
        acts_per_agent={"alice": 0, "hatter": 1},
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_priority_window_opened() -> None:
    event = PriorityWindowOpened(
        timestamp=T0,
        meeting_thread_id="m4",
        phase_name="red",
        agent_id="alice",
        rotation_index=0,
        window_index_in_phase=2,
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_agent_acted() -> None:
    event = AgentActed(
        timestamp=T0,
        meeting_thread_id="m4",
        phase_name="red",
        agent_id="alice",
        rotation_index=0,
        utterance_id="utt-abc",
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_agent_passed_with_reason() -> None:
    event = AgentPassed(
        timestamp=T0,
        meeting_thread_id="m4",
        phase_name="red",
        agent_id="hatter",
        rotation_index=0,
        reason="nothing to add",
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_roundtrip_rotation_completed() -> None:
    event = RotationCompleted(
        timestamp=T0,
        meeting_thread_id="m4",
        phase_name="red",
        rotation_index=1,
    )
    decoded = from_jsonl(to_jsonl(event))
    assert decoded == event


def test_unknown_kind_raises() -> None:
    """Forward-compat: a JSONL line written by a newer wonderland
    surfaces a clear error rather than silently dropping events."""
    with pytest.raises(UnknownEventKind, match="GremlinSpotted"):
        from_jsonl('{"kind":"GremlinSpotted","data":{}}')
