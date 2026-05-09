"""Utterance schema — the atomic unit of agent communication.

Per WONDERLAND_SPEC §4. Every agent communication is an Utterance. The
speech_act typing is doing identity work: different characters have
different distributions over which acts they perform, and the substantive
vs procedural split prevents the orchestrator drifting into domain
content.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from ulid import ULID


def _new_ulid() -> str:
    return str(ULID())


def _now_utc() -> datetime:
    return datetime.now(UTC)


class SpeechAct(StrEnum):
    # Substantive — issued by domain agents
    DIRECTIVE = "directive"
    STORY = "story"
    QUESTION = "question"
    TICKET = "ticket"
    FEATURE = "feature"
    PROPOSAL = "proposal"
    CONCERN = "concern"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    TEST_SCENARIO = "test_scenario"
    RULING = "ruling"
    OBSERVATION = "observation"
    REFRAME = "reframe"
    DEFERENCE = "deference"
    CONTRACT_NOTE = "contract_note"

    # Procedural — issued primarily by the Dodo
    NUDGE = "nudge"
    COMPOSITION = "composition"
    ESCALATION = "escalation"
    ACKNOWLEDGMENT = "acknowledgment"
    # Procedural — any agent can issue (roster mutation, Block 2c)
    INVITE = "invite"
    # Procedural — first-class "I have nothing load-bearing to add"
    # signal in phased meetings (analysis 033 / P9). Distinct from
    # silence: silence means "engagement policy didn't fire"; PASS
    # means "I had a priority window and chose not to act."
    PASS = "pass"


SUBSTANTIVE_ACTS: frozenset[SpeechAct] = frozenset(
    {
        SpeechAct.DIRECTIVE,
        SpeechAct.STORY,
        SpeechAct.QUESTION,
        SpeechAct.TICKET,
        SpeechAct.FEATURE,
        SpeechAct.PROPOSAL,
        SpeechAct.CONCERN,
        SpeechAct.IMPLEMENTATION,
        SpeechAct.REVIEW,
        SpeechAct.TEST_SCENARIO,
        SpeechAct.RULING,
        SpeechAct.OBSERVATION,
        SpeechAct.REFRAME,
        SpeechAct.DEFERENCE,
        SpeechAct.CONTRACT_NOTE,
    }
)

PROCEDURAL_ACTS: frozenset[SpeechAct] = frozenset(
    {
        SpeechAct.NUDGE,
        SpeechAct.COMPOSITION,
        SpeechAct.ESCALATION,
        SpeechAct.ACKNOWLEDGMENT,
        SpeechAct.INVITE,
        SpeechAct.PASS,
    }
)


def is_substantive(act: SpeechAct) -> bool:
    return act in SUBSTANTIVE_ACTS


def is_procedural(act: SpeechAct) -> bool:
    return act in PROCEDURAL_ACTS


class Stance(StrEnum):
    IN_CHARACTER = "in_character"
    OUT_OF_CHARACTER = "out_of_character"
    META = "meta"


class AffectVector(BaseModel):
    """Per-utterance affective state — Thymos-equivalent.

    Fixed core dimensions provide a shared vocabulary across agents for
    telemetry and engagement-policy heuristics. Per-character signals
    (Hatter's manic energy, Caterpillar's slow consideration) live in
    `extras` until they prove general enough to promote.
    """

    model_config = ConfigDict(frozen=True)

    arousal: float = Field(default=0.0, ge=-1.0, le=1.0)
    valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    urgency: float = Field(default=0.0, ge=-1.0, le=1.0)
    extras: dict[str, float] = Field(default_factory=dict)


class AgentIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    constitution_version: str


class Artifact(BaseModel):
    """Structured output attached to an utterance.

    `kind` is the discriminator (ticket, adr, test_scenario, review,
    ruling, runbook, implementation, ...). Per-kind payload schemas are
    enforced by per-character artifact handlers (see P5 roadmap), not
    here — the schema layer keeps the bus generic.
    """

    model_config = ConfigDict(frozen=True)

    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)


class UtteranceContent(BaseModel):
    model_config = ConfigDict(frozen=True)

    body: str
    artifacts: list[Artifact] = Field(default_factory=list)


class Utterance(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=_new_ulid)
    thread_id: str
    parent_id: str | None = None

    speaker: AgentIdentity
    addressed_to: list[AgentIdentity] | Literal["caucus"]

    speech_act: SpeechAct
    content: UtteranceContent

    references: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_now_utc)

    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    stance: Stance = Stance.IN_CHARACTER
    affect: AffectVector = Field(default_factory=AffectVector)

    is_seed: bool = False
    """True when this utterance was published as a seed by Runner.convene
    rather than emitted as a fresh turn in the current thread. Seeds are
    context (visible in thread history, counted in engagement-state
    annotations) but not engagement triggers — agents should *see* them
    without reacting as if they were just spoken. Engagement rules
    short-circuit to ALMOST_NEVER for seeded utterances; deliberate()
    still has the body and any artifacts in its prompt window."""

    recipients: frozenset[str] | None = None
    """When set, the bus delivers this utterance only to subscribers
    whose name is in the set, regardless of the thread's roster. None
    (the default) preserves the existing roster-only fan-out.

    This is the priority-gate primitive for phased meetings (analysis
    033 / P9). The phase orchestrator publishes a window-open utterance
    with ``recipients={priority_agent}`` so only that agent sees it.
    Observer-tier subscribers (``bypass_roster=True``) still see every
    utterance — measurement isn't affected, only delivery."""
