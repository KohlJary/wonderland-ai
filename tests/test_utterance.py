"""Tests for the Utterance schema."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from wonderland import (
    PROCEDURAL_ACTS,
    SUBSTANTIVE_ACTS,
    AffectVector,
    AgentIdentity,
    Artifact,
    SpeechAct,
    Stance,
    Utterance,
    UtteranceContent,
    is_procedural,
    is_substantive,
)

# ---------- SpeechAct categorization ----------


def test_substantive_and_procedural_partition_the_enum() -> None:
    """Every SpeechAct value belongs to exactly one category."""
    all_acts = set(SpeechAct)
    assert all_acts == SUBSTANTIVE_ACTS | PROCEDURAL_ACTS
    assert set() == SUBSTANTIVE_ACTS & PROCEDURAL_ACTS


def test_substantive_count_matches_spec() -> None:
    # 13 from WONDERLAND_SPEC §6 + contract_note added in P6.T35
    # + feature added for the M2.5 composition phase.
    assert len(SUBSTANTIVE_ACTS) == 15


def test_procedural_count_matches_spec() -> None:
    # 4 from WONDERLAND_SPEC §6 + invite added in P6 Block 2c +
    # pass added for phased meetings (analysis 033 / P9 T58a).
    assert len(PROCEDURAL_ACTS) == 6


def test_pass_is_procedural() -> None:
    """PASS is the first-class 'I had a window and chose not to act'
    signal in phased meetings — procedural by category."""
    assert is_procedural(SpeechAct.PASS)
    assert not is_substantive(SpeechAct.PASS)


@pytest.mark.parametrize(
    "act",
    [
        SpeechAct.DIRECTIVE,
        SpeechAct.PROPOSAL,
        SpeechAct.TEST_SCENARIO,
        SpeechAct.RULING,
        SpeechAct.DEFERENCE,
    ],
)
def test_is_substantive(act: SpeechAct) -> None:
    assert is_substantive(act)
    assert not is_procedural(act)


@pytest.mark.parametrize(
    "act",
    [
        SpeechAct.NUDGE,
        SpeechAct.COMPOSITION,
        SpeechAct.ESCALATION,
        SpeechAct.ACKNOWLEDGMENT,
    ],
)
def test_is_procedural(act: SpeechAct) -> None:
    assert is_procedural(act)
    assert not is_substantive(act)


# ---------- AffectVector ----------


def test_affect_vector_defaults_are_neutral() -> None:
    a = AffectVector()
    assert a.arousal == 0.0
    assert a.valence == 0.0
    assert a.urgency == 0.0
    assert a.extras == {}


def test_affect_vector_accepts_signed_values() -> None:
    a = AffectVector(arousal=0.7, valence=-0.3, urgency=1.0)
    assert a.arousal == 0.7
    assert a.valence == -0.3
    assert a.urgency == 1.0


@pytest.mark.parametrize("field", ["arousal", "valence", "urgency"])
def test_affect_vector_bounds(field: str) -> None:
    with pytest.raises(ValidationError):
        AffectVector(**{field: 1.5})
    with pytest.raises(ValidationError):
        AffectVector(**{field: -1.5})


def test_affect_vector_extras_carry_arbitrary_named_axes() -> None:
    a = AffectVector(extras={"manic": 0.9, "wry": 0.4})
    assert a.extras["manic"] == 0.9
    assert a.extras["wry"] == 0.4


def test_affect_vector_is_frozen() -> None:
    a = AffectVector()
    with pytest.raises(ValidationError):
        a.arousal = 0.5  # type: ignore[misc]


# ---------- AgentIdentity ----------


def test_agent_identity_is_frozen() -> None:
    cat = AgentIdentity(name="cheshire_cat", constitution_version="0.1")
    with pytest.raises(ValidationError):
        cat.name = "rabbit"  # type: ignore[misc]


def test_agent_identity_equality_is_structural() -> None:
    a = AgentIdentity(name="cheshire_cat", constitution_version="0.1")
    b = AgentIdentity(name="cheshire_cat", constitution_version="0.1")
    c = AgentIdentity(name="cheshire_cat", constitution_version="0.2")
    assert a == b
    assert a != c


# ---------- Artifact ----------


def test_artifact_payload_is_flexible() -> None:
    adr = Artifact(
        kind="adr",
        payload={
            "number": 1,
            "title": "Use Redis Streams for the Caucus",
            "tradeoffs": ["familiar ops", "single-region default"],
        },
    )
    assert adr.kind == "adr"
    assert adr.payload["number"] == 1


def test_artifact_kind_is_required() -> None:
    with pytest.raises(ValidationError):
        Artifact(payload={})  # type: ignore[call-arg]


# ---------- Utterance ----------


def _cat() -> AgentIdentity:
    return AgentIdentity(name="cheshire_cat", constitution_version="0.1")


def _rabbit() -> AgentIdentity:
    return AgentIdentity(name="white_rabbit", constitution_version="0.1")


def test_utterance_default_id_is_ulid_string() -> None:
    u = Utterance(
        thread_id="01JABCDEF",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    # ULIDs are 26-char Crockford base32
    assert isinstance(u.id, str)
    assert len(u.id) == 26


def test_utterance_default_timestamp_is_utc() -> None:
    u = Utterance(
        thread_id="t",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    assert u.timestamp.tzinfo is not None
    assert u.timestamp.utcoffset().total_seconds() == 0


def test_utterance_caucus_broadcast() -> None:
    u = Utterance(
        thread_id="t",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    assert u.addressed_to == "caucus"


def test_utterance_addressed_to_specific_agents() -> None:
    u = Utterance(
        thread_id="t",
        speaker=_cat(),
        addressed_to=[_rabbit()],
        speech_act=SpeechAct.DEFERENCE,
        content=UtteranceContent(body="this is your call"),
    )
    assert isinstance(u.addressed_to, list)
    assert u.addressed_to[0].name == "white_rabbit"


def test_utterance_with_artifacts() -> None:
    adr = Artifact(kind="adr", payload={"number": 1})
    u = Utterance(
        thread_id="t",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="proposing X", artifacts=[adr]),
    )
    assert u.content.artifacts[0].kind == "adr"


def test_utterance_is_frozen() -> None:
    u = Utterance(
        thread_id="t",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    with pytest.raises(ValidationError):
        u.confidence = 0.5  # type: ignore[misc]


def test_utterance_confidence_bounds() -> None:
    base = dict(
        thread_id="t",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    Utterance(**base, confidence=0.0)
    Utterance(**base, confidence=1.0)
    with pytest.raises(ValidationError):
        Utterance(**base, confidence=1.1)
    with pytest.raises(ValidationError):
        Utterance(**base, confidence=-0.1)


def test_utterance_default_stance_is_in_character() -> None:
    u = Utterance(
        thread_id="t",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    assert u.stance == Stance.IN_CHARACTER


def test_utterance_round_trip_json() -> None:
    original = Utterance(
        thread_id="01JFOO",
        parent_id="01JBAR",
        speaker=_cat(),
        addressed_to=[_rabbit()],
        speech_act=SpeechAct.REFRAME,
        content=UtteranceContent(
            body="what would have to be true for the choice to matter?",
            artifacts=[Artifact(kind="adr", payload={"number": 7})],
        ),
        references=["01JBAZ"],
        confidence=0.8,
        stance=Stance.IN_CHARACTER,
        affect=AffectVector(arousal=-0.2, valence=0.1, extras={"oblique": 0.6}),
    )
    serialized = original.model_dump_json()
    parsed_dict = json.loads(serialized)
    rehydrated = Utterance.model_validate(parsed_dict)
    assert rehydrated == original


def test_utterance_thread_id_required() -> None:
    with pytest.raises(ValidationError):
        Utterance(  # type: ignore[call-arg]
            speaker=_cat(),
            addressed_to="caucus",
            speech_act=SpeechAct.PROPOSAL,
            content=UtteranceContent(body="..."),
        )


def test_utterance_recipients_default_is_none() -> None:
    """Default recipients=None means open delivery via the existing
    roster. The priority-gate primitive (T58a) is opt-in."""
    u = Utterance(
        thread_id="t",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    assert u.recipients is None


def test_utterance_recipients_round_trip_json() -> None:
    """Recipients survives JSONL serialization (snapshots + replay)."""
    import json

    original = Utterance(
        thread_id="t",
        speaker=_cat(),
        addressed_to="caucus",
        speech_act=SpeechAct.NUDGE,
        content=UtteranceContent(body="your window"),
        recipients=frozenset({"hatter", "tweedledum"}),
    )
    rehydrated = Utterance.model_validate(json.loads(original.model_dump_json()))
    assert rehydrated.recipients == frozenset({"hatter", "tweedledum"})
