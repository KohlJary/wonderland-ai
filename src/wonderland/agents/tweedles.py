"""Tweedledee + Tweedledum — the implementation pair.

Per tweedledee.md, tweedledum.md, and tweedle_pair_protocol.md
(WONDERLAND_SPEC §5). The Tweedles are the framework's first paired
agents — each has a singular self-model AND a shared pair-protocol.
This module instantiates both because the pair is a unit per the
protocol; splitting them into separate modules would obscure that
the engagement rules and output protocol are mirror-image variants
of the same shape.

Constitution loading is doubled: each Tweedle's identity carries
its own constitution text *concatenated with* the shared
``tweedle_pair_protocol.md``, so both texts ride in the cached
system prefix on every deliberation. This makes the pair-protocol
part of who the Tweedle is, not a one-off instruction.

Runtime shape mirrors the other agents: load constitution(s), wire
engagement rules from §III, override deliberate() with a JSON
output protocol, persist implementations through an
ImplementationRegistry. The two agents share TweedleResponse and
the parser; engagement rules differ only in which sibling they're
oriented toward.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from wonderland.agent import Context, WonderlandAgent
from wonderland.engagement import (
    EngagementRules,
    addressed_to,
    almost_never,
    always,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import Identity, load_constitution
from wonderland.implementation import (
    ImplementationPayload,
    ImplementationRegistry,
    ImplementationSide,
)
from wonderland.llm import CachedBlock
from wonderland.utterance import (
    Artifact,
    SpeechAct,
    Utterance,
    UtteranceContent,
)

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.llm import LLMClient
    from wonderland.memory import AgentMemory


TWEEDLEDEE_NAME = "tweedledee"
TWEEDLEDUM_NAME = "tweedledum"
PAIR_PROTOCOL_FILENAME = "tweedle_pair_protocol.md"


# --------------------------------------------------------------------- #
# Constitution loading — own constitution + shared pair protocol
# --------------------------------------------------------------------- #


def _default_constitutions_root() -> Path:
    """Path to constitutions/ relative to this package layout.

    Mirrors ``wonderland.identity._default_constitutions_root`` — kept
    local to avoid coupling to that module's private surface.
    """
    return Path(__file__).resolve().parent.parent.parent.parent / "constitutions"


def _load_paired_identity(
    self_name: str, constitutions_root: Path | None
) -> Identity:
    """Load a Tweedle identity with the pair protocol concatenated.

    The pair protocol is part of who each Tweedle is per
    ``tweedle_pair_protocol.md`` §VI: "the pair's memory of itself is
    part of the pair's identity." Concatenating into the cached
    constitution prefix keeps the protocol on every deliberation
    without paying for it as an uncached layer.
    """
    identity = load_constitution(self_name, root=constitutions_root)
    root = constitutions_root or _default_constitutions_root()
    pair_path = root / PAIR_PROTOCOL_FILENAME
    pair_text = pair_path.read_text(encoding="utf-8")
    combined = (
        f"{identity.constitution_text.rstrip()}\n\n"
        f"---\n\n"
        f"{pair_text.rstrip()}\n"
    )
    return replace(identity, constitution_text=combined)


# --------------------------------------------------------------------- #
# Engagement rules — tweedledee.md §III / tweedledum.md §III as data
# --------------------------------------------------------------------- #


def _tweedle_rules(*, self_name: str, sibling_name: str) -> EngagementRules:
    """Shared §III engagement policy with the sibling reference parameterized.

    The two Tweedles' engagement rules are mirror-image — each engages
    ALWAYS with concerns from their sibling about the contract,
    SELECTIVELY with non-contract concerns from the sibling, RARELY
    with sibling implementations that don't touch the contract. The
    only difference is which name fills "sibling".
    """
    return EngagementRules.of(
        # ALWAYS — work assignment + the contract-negotiation surface
        always(SpeechAct.TICKET, condition=speaker_is("white_rabbit")),
        always(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat")),
        always(SpeechAct.STORY, condition=speaker_is("alice")),
        always(SpeechAct.CONCERN, condition=speaker_is(sibling_name)),
        always(SpeechAct.TEST_SCENARIO, condition=speaker_is("mad_hatter")),
        always(SpeechAct.REVIEW, condition=speaker_is("caterpillar")),
        always(SpeechAct.QUESTION, condition=addressed_to(self_name)),
        # SELECTIVELY — refined by deliberate()
        selectively(SpeechAct.RULING, condition=speaker_is("queen_of_hearts")),
        selectively(SpeechAct.OBSERVATION, condition=speaker_is("dormouse")),
        # RARELY — sibling implementations that don't touch the contract are
        # not the Tweedle's primary attention surface (per §III)
        rarely(SpeechAct.IMPLEMENTATION, condition=speaker_is(sibling_name)),
        rarely(SpeechAct.DEFERENCE),
        # ALMOST_NEVER — explicit guards against the §VIII Architectural-drift
        # failure mode. The Tweedles don't issue these speech acts; engaging
        # with same-typed utterances from non-canonical speakers would just
        # be domain-leak noise.
        almost_never(SpeechAct.STORY),  # not from Alice
        almost_never(SpeechAct.PROPOSAL),  # not from Cat
        almost_never(SpeechAct.TICKET),  # not from Rabbit
        almost_never(SpeechAct.RULING),  # not from Queen
        almost_never(SpeechAct.TEST_SCENARIO),  # not from Hatter
        almost_never(SpeechAct.REVIEW),  # not from Caterpillar
        almost_never(SpeechAct.OBSERVATION),  # not from Dormouse
        almost_never(SpeechAct.DIRECTIVE),
    )


def tweedledee_rules() -> EngagementRules:
    """Tweedledee's §III engagement policy — sibling = Tweedledum."""
    return _tweedle_rules(self_name=TWEEDLEDEE_NAME, sibling_name=TWEEDLEDUM_NAME)


def tweedledum_rules() -> EngagementRules:
    """Tweedledum's §III engagement policy — sibling = Tweedledee."""
    return _tweedle_rules(self_name=TWEEDLEDUM_NAME, sibling_name=TWEEDLEDEE_NAME)


# --------------------------------------------------------------------- #
# LLM output protocol — shared between the pair
# --------------------------------------------------------------------- #


TweedleDecision = Literal[
    "implementation",
    "concern",
    "question",
    "deference",
    "silence",
]


class TweedleResponse(BaseModel):
    """Structured JSON either Tweedle returns from deliberate().

    When ``decision == "implementation"``, ``implementations`` must
    contain at least one ``ImplementationPayload``. The default is one
    — a Tweedle ships one piece of work at a time — but the schema
    permits more so a batched landing of related work can be reported
    in one turn.
    """

    decision: TweedleDecision
    body: str = ""
    implementations: list[ImplementationPayload] = Field(default_factory=list)

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # Live Haiku 4.5 sometimes emits explicit nulls for omitted fields.
        # Coerce to default per the established pattern.
        return "" if v is None else v

    @field_validator("implementations", mode="before")
    @classmethod
    def _implementations_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "implementation" and not self.implementations:
            raise ValueError(
                "TweedleResponse: decision='implementation' requires at least "
                "one entry in `implementations`. Choose a different decision "
                "(concern/question/etc.) or include the implementation you "
                "intended to ship."
            )


def _build_protocol(side: ImplementationSide, sibling_name: str) -> str:
    """Construct the per-side output protocol.

    Both Tweedles share most of the protocol — the differences are
    the side label, the field-population guidance, and which sibling
    they're negotiating with. Building the protocol per side avoids
    awkward "fill in either UI states OR invariants" hedging.
    """
    if side is ImplementationSide.FRONTEND:
        side_fields = (
            '      "ui_states_implemented": ["loading", "empty", "error-recoverable", "..."],\n'
            '      "client_state": "what state lives on the client and how it reconciles with server state",\n'
        )
        side_guidance = (
            "You are the frontend Tweedle. Populate `ui_states_implemented` with the "
            "named states the user might encounter (loading / empty / error-recoverable / "
            "error-unrecoverable / offline-queued / stale / pending-sync / etc.) and "
            "`client_state` with what state lives on the client, why, and how it "
            "reconciles with the canonical server state. Leave `invariants_enforced`, "
            "`schema_changes`, and `failure_modes_handled` empty — those are Tweedledum's."
        )
    else:
        side_fields = (
            '      "invariants_enforced": ["a message has exactly one sender", "..."],\n'
            '      "schema_changes": "migrations introduced, with backward-compatibility notes",\n'
            '      "failure_modes_handled": ["worker crash mid-message: dead-letter", "..."],\n'
        )
        side_guidance = (
            "You are the backend Tweedle. Populate `invariants_enforced` with named "
            "invariants this implementation maintains, each with how (DB constraint, "
            "validation, transactional boundary, etc.); `schema_changes` with any "
            "migrations introduced and their backward-compatibility properties; "
            "`failure_modes_handled` with named failure modes and their handling "
            "behavior (retry / dead-letter / propagate / fallback). Leave "
            "`ui_states_implemented` and `client_state` empty — those are Tweedledee's."
        )

    return f"""\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{{
  "decision": "implementation" | "concern" | "question" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "implementations": [               // include ONLY when decision is "implementation"
    {{
      "title": "short summary of what shipped, e.g. 'Translation message subscription'",
      "side": "{side.value}",
      "ticket_reference": "the Rabbit ticket slug or number this implements",
      "approach_summary": "what the code actually does, in concrete terms",
      "contract": "the contract version + shape this honors, e.g. 'message-envelope v3 (translation_status enum + source_lang FK)'",
      "files_touched": ["src/path/to/file.py: brief description of the change", "..."],
      "open_questions_for_pair": ["specific question for {sibling_name} about contract or coordination"],
      "ready_for_review": true | false,
      "known_limitations": ["things this doesn't yet handle, with severity"],
{side_fields}    }}
  ]
}}
```

**Contract is non-negotiable.** Per the Tweedle Pair Protocol §II,
"implicit contracts are bugs in the making." The schema rejects
empty-contract implementations. Cite the OpenAPI revision, schema
version, message envelope version, or whatever shape your agreement
with {sibling_name} takes. If you're shipping a contract change, name
the new version and reference the Contract Note that authorized it.

**Ticket reference is non-negotiable.** Implementations must trace to
a Rabbit ticket. If the work isn't ticketed, the move is to ask the
Rabbit to ticket it before shipping — not to ship and backfill.

{side_guidance}

`ready_for_review` is the explicit Caterpillar engagement gate per
§VI. Set it to `false` while you're still iterating; set it to `true`
when the implementation is ready for review and you're prepared to
respond to the findings.

Domain discipline matters. You do **not** propose architecture (the
Cat's domain), write tickets (the Rabbit's), generate stories
(Alice's), write tests (the Hatter's), review code quality (the
Caterpillar's), rule on security (the Queen's), or report production
behavior (the Dormouse's). When the work pulls you across one of
those lines, choose `concern` (raise the issue to its owner) or
`deference` (explicit handoff).

Speak in concrete, implementation-grounded sentences. Ask {sibling_name}
specific questions when the contract is unclear. Use
`open_questions_for_pair` for those questions inline; that's how the
contract negotiation stays explicit per the Pair Protocol §IV.
Concede readily when {sibling_name}'s point is correct; press when
yours is. The argument is the work.
"""


_OUTPUT_PROTOCOL_FRONTEND = _build_protocol(
    ImplementationSide.FRONTEND, TWEEDLEDUM_NAME
)
_OUTPUT_PROTOCOL_BACKEND = _build_protocol(
    ImplementationSide.BACKEND, TWEEDLEDEE_NAME
)


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class TweedleResponseParseError(ValueError):
    """A Tweedle's LLM response did not parse into a valid TweedleResponse."""


def parse_tweedle_response(text: str) -> TweedleResponse:
    """Extract the fenced JSON block from `text` and validate it."""
    match = _JSON_BLOCK.search(text)
    if match is None:
        candidate = text.strip()
        if not (candidate.startswith("{") and candidate.endswith("}")):
            raise TweedleResponseParseError(
                "no JSON block found in Tweedle response"
            )
        raw = candidate
    else:
        raw = match.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TweedleResponseParseError(
            f"Tweedle response was not valid JSON: {exc}"
        ) from exc
    try:
        return TweedleResponse.model_validate(data)
    except ValidationError as exc:
        raise TweedleResponseParseError(
            f"Tweedle response failed schema validation: {exc}"
        ) from exc


# --------------------------------------------------------------------- #
# Shared agent base — keeps the two Tweedles synchronized
# --------------------------------------------------------------------- #


class _TweedleBase(WonderlandAgent):
    """Shared implementation. Subclasses set side, name, rules, and protocol.

    Mirrors the Cat / Rabbit / Alice / Hatter / Caterpillar / Queen /
    Dormouse pattern. The only inter-Tweedle difference is which
    sibling each is oriented toward; everything else is shared.
    """

    SIDE: ImplementationSide
    PROTOCOL: str

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        implementation_registry: ImplementationRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = _load_paired_identity(self._self_name(), constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(self._rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._implementation_registry = implementation_registry

    # Subclasses provide these — kept as classmethods so the rules table
    # is constructible without instantiation (useful in tests).
    @classmethod
    def _self_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def _rules(cls) -> EngagementRules:
        raise NotImplementedError

    @property
    def implementation_registry(self) -> ImplementationRegistry | None:
        return self._implementation_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution + pair protocol —
        # all three are invariant per Tweedle.
        system.insert(1, CachedBlock(self.PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = parse_tweedle_response(result.text)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "implementation":
            artifacts.extend(
                self._record_implementations(response.implementations)
            )

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

    def _record_implementations(
        self, payloads: list[ImplementationPayload]
    ) -> list[Artifact]:
        if self._implementation_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._implementation_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="implementation",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "side": record.side.value,
                        "ticket_reference": record.ticket_reference,
                        "contract": record.contract,
                        "ready_for_review": record.ready_for_review,
                        "path": str(record.path),
                    },
                )
            )
        return artifacts

    @staticmethod
    def _derive_threading(context: Context) -> tuple[str, str | None]:
        if not context.triggers:
            return "", None
        first = context.triggers[0]
        return first.thread_id, first.id


class Tweedledee(_TweedleBase):
    """Tweedledee: frontend Tweedle, builds from the user's standpoint inward."""

    SIDE = ImplementationSide.FRONTEND
    PROTOCOL = _OUTPUT_PROTOCOL_FRONTEND

    @classmethod
    def _self_name(cls) -> str:
        return TWEEDLEDEE_NAME

    @classmethod
    def _rules(cls) -> EngagementRules:
        return tweedledee_rules()


class Tweedledum(_TweedleBase):
    """Tweedledum: backend Tweedle, builds from the data outward."""

    SIDE = ImplementationSide.BACKEND
    PROTOCOL = _OUTPUT_PROTOCOL_BACKEND

    @classmethod
    def _self_name(cls) -> str:
        return TWEEDLEDUM_NAME

    @classmethod
    def _rules(cls) -> EngagementRules:
        return tweedledum_rules()


__all__ = [
    "PAIR_PROTOCOL_FILENAME",
    "TWEEDLEDEE_NAME",
    "TWEEDLEDUM_NAME",
    "TweedleDecision",
    "TweedleResponse",
    "TweedleResponseParseError",
    "Tweedledee",
    "Tweedledum",
    "parse_tweedle_response",
    "tweedledee_rules",
    "tweedledum_rules",
]
