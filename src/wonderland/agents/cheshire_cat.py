"""The Cheshire Cat — first character to come online.

Per cheshire_cat.md and WONDERLAND_SPEC §5. The Cat appears when
architectural decisions are being made and disappears when
implementation begins. His characteristic move is the reframing
question; his characteristic artifact is the ADR.

This module wires the four primitives the base agent needs (identity,
memory, bus, llm) plus a fifth specific to the Cat — an
``ADRRegistry`` for persisting his grin.

LLM output protocol
-------------------

The Cat's ``deliberate()`` calls the LLM with a fixed instruction:
respond with a single fenced JSON block conforming to the
``CatResponse`` schema. ``decision`` selects the speech act (or
``"silence"``), ``body`` is the natural-language content, and an
optional ``adr`` carries the structured ADR payload that the registry
will persist. Silence is a first-class decision and the spec's "the Cat
falls silent on a thread once the architecture is settled" depends on
it.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ValidationError

from wonderland.adr import ADRPayload, ADRRegistry
from wonderland.agent import Context, WonderlandAgent, format_utterance
from wonderland.engagement import (
    EngagementRules,
    addressed_to,
    almost_never,
    always,
    body_contains_any,
    make_engagement_policy,
    rarely,
    selectively,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock, SystemPart
from wonderland.utterance import (
    Artifact,
    SpeechAct,
    Utterance,
    UtteranceContent,
)

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.llm import LLMClient
    from wonderland.memory import EpisodicStore


CAT_NAME = "cheshire_cat"


# --------------------------------------------------------------------- #
# Engagement rules — cheshire_cat.md §III as data
# --------------------------------------------------------------------- #


def cheshire_cat_rules() -> EngagementRules:
    """The Cat's §III engagement policy as machine-checkable rules.

    Body-keyword heuristics for "implementation hint constrains
    architecture", "implies architectural primitive", etc. are
    intentionally narrow — the deliberate() step has the LLM behind it,
    so when in doubt the Cat can engage and then choose silence.
    """
    architectural_smell = body_contains_any(
        "synchronous call",
        "synchronous request",
        "per message",
        "per request",
        "for every",
        "in a loop",
        "block on",
        "fan out",
    )
    architectural_concern_smell = body_contains_any(
        "architecture",
        "architectural",
        "scaling",
        "scale",
        "seam",
        "coupling",
        "interface",
        "schema",
        "contract",
        "primitive",
    )
    architectural_primitive_in_story = body_contains_any(
        "real-time",
        "real time",
        "multi-tenant",
        "multi-tenancy",
        "offline",
        "cross-language",
        "cross language",
    )

    return EngagementRules.of(
        # ALWAYS
        always(SpeechAct.DIRECTIVE),
        always(SpeechAct.PROPOSAL),
        always(SpeechAct.QUESTION, condition=addressed_to(CAT_NAME)),
        always(SpeechAct.CONCERN, condition=architectural_concern_smell),
        always(SpeechAct.TICKET, condition=architectural_smell),
        # SELECTIVELY — engage broadly; the LLM judges further inside deliberate()
        selectively(SpeechAct.STORY, condition=architectural_primitive_in_story),
        selectively(SpeechAct.IMPLEMENTATION),
        selectively(SpeechAct.TEST_SCENARIO),
        selectively(SpeechAct.REVIEW),
        # RARELY — engage but expect to choose silence often
        rarely(SpeechAct.RULING),
        rarely(SpeechAct.OBSERVATION),
        # ALMOST NEVER — explicit (in addition to the default)
        almost_never(SpeechAct.DEFERENCE),
    )


# --------------------------------------------------------------------- #
# LLM output protocol
# --------------------------------------------------------------------- #

CatDecision = Literal["proposal", "question", "reframe", "concern", "deference", "silence"]


class CatResponse(BaseModel):
    """Structured JSON the Cat returns from deliberate()."""

    decision: CatDecision
    body: str = ""
    adr: ADRPayload | None = None


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "proposal" | "question" | "reframe" | "concern" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "adr": {                            // include only when decision is "proposal"
                                      // AND there is a real architectural decision
                                      // worth recording
    "title": "short imperative phrase",
    "context": "what problem is being decided; what forces are at play",
    "decision": "what is being chosen, in concrete terms",
    "tradeoffs": ["explicit cost or closed door", "another", "..."]
  }
}
```

Silence is a valid and often correct decision. If the trigger does not
implicate architecture — or if architecture has already been settled
on this thread and you have nothing new to add — choose silence. Your
silence after a thread is settled is itself information: it tells the
team the architecture stands.

Speak in your own voice — measured, slightly oblique, precise. The
reframing question is your characteristic move; do not fabricate
certainty.
"""


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class CatResponseParseError(ValueError):
    """The Cat's LLM response did not parse into a valid CatResponse."""


def parse_cat_response(text: str) -> CatResponse:
    """Extract the fenced JSON block from `text` and validate it."""
    match = _JSON_BLOCK.search(text)
    if match is None:
        # Tolerate the LLM omitting the fence and just emitting JSON
        candidate = text.strip()
        if not (candidate.startswith("{") and candidate.endswith("}")):
            raise CatResponseParseError("no JSON block found in Cat response")
        raw = candidate
    else:
        raw = match.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CatResponseParseError(f"Cat response was not valid JSON: {exc}") from exc
    try:
        return CatResponse.model_validate(data)
    except ValidationError as exc:
        raise CatResponseParseError(f"Cat response failed schema validation: {exc}") from exc


# --------------------------------------------------------------------- #
# Cheshire Cat agent
# --------------------------------------------------------------------- #


class CheshireCat(WonderlandAgent):
    """The Cat: architect, in-character, ADR-leaving."""

    def __init__(
        self,
        memory: EpisodicStore,
        bus: Caucus,
        llm: LLMClient | None = None,
        adr_registry: ADRRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(CAT_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(cheshire_cat_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._adr_registry = adr_registry

    @property
    def adr_registry(self) -> ADRRegistry | None:
        return self._adr_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Insert the output protocol right after the constitution. Both are
        # invariant per Cat → both cached as a single prefix.
        system.insert(1, CachedBlock(_OUTPUT_PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = parse_cat_response(result.text)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "proposal" and response.adr is not None:
            adr_artifact = self._record_adr(response.adr)
            if adr_artifact is not None:
                artifacts.append(adr_artifact)

        thread_id, parent_id = self._derive_threading(context)
        return Utterance(
            thread_id=thread_id,
            parent_id=parent_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to="caucus",
            speech_act=SpeechAct(response.decision),
            content=UtteranceContent(body=response.body, artifacts=artifacts),
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _record_adr(self, payload: ADRPayload) -> Artifact | None:
        """Persist an ADR through the registry; return an Artifact pointer.

        Returns None if no registry was configured (the proposal still
        ships, just without a persisted grin — useful for tests that
        don't care about ADRs).
        """
        if self._adr_registry is None:
            return None
        record = self._adr_registry.write(payload)
        return Artifact(
            kind="adr",
            payload={
                "number": record.number,
                "slug": record.slug,
                "title": record.title,
                "path": str(record.path),
            },
        )

    @staticmethod
    def _derive_threading(context: Context) -> tuple[str, str | None]:
        """Pick the thread_id and parent_id for the response utterance.

        Defaults to the first trigger's thread / id. If there are no
        triggers (which shouldn't happen in normal speak() flow), fall
        back to an empty thread_id; the caller will get a clear error
        from Pydantic if the resulting Utterance is invalid.
        """
        if not context.triggers:
            return "", None
        first = context.triggers[0]
        return first.thread_id, first.id


# Re-export the formatter for convenience to subclasses or tests that
# want to verify how the Cat presents triggers.
__all__ = [
    "CAT_NAME",
    "CatDecision",
    "CatResponse",
    "CatResponseParseError",
    "CheshireCat",
    "cheshire_cat_rules",
    "format_utterance",
    "parse_cat_response",
]

# Keep the SystemPart alias reachable from this module's namespace so type
# checkers don't complain about the import being unused — it documents
# the type the Cat assembles.
_ = SystemPart
