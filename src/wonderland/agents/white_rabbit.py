"""The White Rabbit — second character to come online.

Per white_rabbit.md and WONDERLAND_SPEC §5. The Rabbit decomposes work
into tickets with explicit scope, dependencies, and estimates. He
asks "by when?" persistently. He redirects architectural and
implementation suggestions to the agents who own those domains. He
keeps the burndown honest.

The runtime shape mirrors the Cheshire Cat in T11 — load constitution,
wire engagement rules from §III, override deliberate() with an LLM
output protocol that produces structured JSON, persist any artifacts
through the appropriate registry. The Rabbit's primary artifact is
the Ticket (T12); a single Rabbit turn can issue multiple tickets
because decomposition produces a set, not one at a time.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator

from wonderland.agent import Context, WonderlandAgent
from wonderland.engagement import (
    EngagementRules,
    addressed_to,
    almost_never,
    always,
    any_of,
    body_contains_any,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.feature import FeaturePayload, FeatureRegistry
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.parsing import ResponseParseError, extract_and_validate
from wonderland.ticket import TicketPayload, TicketRegistry
from wonderland.utterance import (
    Artifact,
    SpeechAct,
    Utterance,
    UtteranceContent,
    operator_identity,
)

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.llm import LLMClient
    from wonderland.memory import AgentMemory


RABBIT_NAME = "white_rabbit"


# --------------------------------------------------------------------- #
# Engagement rules — white_rabbit.md §III as data
# --------------------------------------------------------------------- #


def white_rabbit_rules() -> EngagementRules:
    """The Rabbit's §III engagement policy as machine-checkable rules.

    Heuristics for the conditional engagements lean permissive — the
    Rabbit engages broadly with anything that *might* affect scope,
    sequence, or schedule, and uses deliberate() to decide silence when
    nothing is actually implicated. Same disposition as the Cat: when
    in doubt, engage and then choose silence.
    """
    scope_or_schedule_words = body_contains_any(
        "scope",
        "sequence",
        "schedule",
        "timeline",
        "deadline",
        "estimate",
        "by when",
        "blocker",
        "blocked",
        "delay",
        "slip",
        "fast-follow",
        "v1",
        "post-launch",
    )
    incident_words = body_contains_any(
        "incident",
        "outage",
        "regression",
        "broken",
        "breaking",
        "down",
        "p0",
        "p1",
    )
    is_tweedle = any_of(speaker_is("tweedledee"), speaker_is("tweedledum"))

    return EngagementRules.of(
        # ALWAYS — INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(RABBIT_NAME)),
        # ALWAYS
        always(SpeechAct.DIRECTIVE),
        always(SpeechAct.STORY),
        always(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat")),
        always(SpeechAct.CONCERN, condition=scope_or_schedule_words),
        always(SpeechAct.IMPLEMENTATION, condition=is_tweedle),
        # SELECTIVELY
        selectively(SpeechAct.TEST_SCENARIO, condition=speaker_is("mad_hatter")),
        selectively(SpeechAct.REVIEW, condition=speaker_is("caterpillar")),
        selectively(SpeechAct.RULING, condition=speaker_is("queen_of_hearts")),
        selectively(SpeechAct.OBSERVATION, condition=incident_words),
        selectively(SpeechAct.QUESTION, condition=scope_or_schedule_words),
        # RARELY
        rarely(SpeechAct.PROPOSAL),  # any non-Cat proposal — odd but possible
        # ALMOST NEVER
        almost_never(SpeechAct.DEFERENCE),
    )


# --------------------------------------------------------------------- #
# LLM output protocol
# --------------------------------------------------------------------- #


RabbitDecision = Literal[
    "ticket",
    "feature",
    "concern",
    "question",
    "question_to_operator",
    "reframe",
    "deference",
    "silence",
]


class RabbitResponse(BaseModel):
    """Structured JSON the Rabbit returns from deliberate().

    When ``decision == "ticket"``, ``tickets`` must contain at least
    one ``TicketPayload`` — a ticket decision without tickets is
    nonsense. Same for ``decision == "feature"`` and ``features``.
    For other decisions, both lists are ignored.
    """

    decision: RabbitDecision
    body: str = ""
    options: list[str] = Field(
        default_factory=list,
        description=(
            "Optional suggested answers when ``decision == "
            "'question_to_operator'``. Each entry becomes a "
            "click-to-submit button in the operator's modal. "
            "Use 2–4 short option strings for binary or n-way "
            "questions where the answer space is bounded; "
            "operator can still type a custom answer. Ignored "
            "when decision is anything else."
        ),
    )
    tickets: list[TicketPayload] = Field(default_factory=list)
    features: list[FeaturePayload] = Field(default_factory=list)

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # The LLM occasionally emits explicit nulls for omitted fields
        # (especially on `silence`). Coerce to default.
        return "" if v is None else v

    @field_validator("tickets", mode="before")
    @classmethod
    def _tickets_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    @field_validator("features", mode="before")
    @classmethod
    def _features_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "ticket" and not self.tickets:
            raise ValueError(
                "RabbitResponse: decision='ticket' requires at least one ticket "
                "in `tickets`. Choose a different decision (concern/question/etc.) "
                "or include the tickets you intended to issue."
            )
        if self.decision == "feature" and not self.features:
            raise ValueError(
                "RabbitResponse: decision='feature' requires at least one feature "
                "in `features`. Features group constituent tickets into user-facing "
                "units; emitting feature-decision without features is nonsense."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "ticket" | "feature" | "concern" | "question" |
              "question_to_operator" | "reframe" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "tickets": [                        // include ONLY when decision is "ticket"
    {
      "title": "short, action-oriented",
      "owner": "<agent name — usually tweedledee or tweedledum>",
      "tier": "v1" | "fast-follow" | "post-launch",
      "estimate": "duration with confidence — e.g., '0.5-1.5 days, 70% confident'",
      "description": "what needs to be done; specific enough to start, generic enough that the owner retains design authority over implementation",
      "sources": ["story or proposal IDs that produced this ticket"],
      "dependencies": {
        "blocks": ["ticket slugs this blocks"],
        "blocked_by": ["ticket slugs that block this"],
        "soft": ["coordination needed but not strict"]
      },
      "acceptance": ["observable conditions of done"],
      "risk": "anything that could blow the estimate"
    }
  ],
  "features": [                       // include ONLY when decision is "feature"
    {
      "title": "user-facing capability name (e.g. 'sign up and claim a homepage URL')",
      "description": "what user-facing thing this feature delivers, in plain language",
      "tickets": ["ticket slugs aggregated into this feature"],
      "personas": ["persona names from M1 stories that this feature serves"],
      "stack_span": "frontend" | "backend" | "full-stack",
      "tier": "v1" | "fast-follow" | "post-launch",
      "sources": ["story slugs whose intent this feature realizes"]
    }
  ]
}
```

Two decision modes are decomposition-shaped:

- `ticket`: atomic work units (the M2 "Rabbit's Errand" mode).
  Tickets are small enough to start, sized for a single owner, with
  named dependencies. This is your default decomposition output.

- `feature`: tickets *grouped* into user-facing units (the M2.5
  "Advice from a Caterpillar" mode, when the convenor asks for
  feature composition). A feature aggregates multiple tickets that
  ship together as a coherent thing the user notices. Always name
  the stack span — "full-stack" features mean both Tweedles need to
  align on the seam in M3, "frontend" or "backend" features can be
  handled one-sided. Always tie the feature back to the personas
  from M1 stories: if you can't name a persona this feature serves,
  the grouping isn't really a feature, it's a bag of tickets.

**`question_to_operator` — escalate to the human operator.** Use
when the team needs a decision only the operator can make: a
schema-vs-directive conflict you can't resolve, scope ambiguity
contracts can't disambiguate, business priority calls between
tickets, "is this v1 or fast-follow" calls when the directive's
silent. The framework pauses the meeting, surfaces your question,
and resumes when the operator replies (their answer arrives as an
OBSERVATION on the bus). Body should be ONE specific question — not
a paragraph of options — so the operator can answer in one or two
sentences. "Should I X or Y?" is the right shape. Reserve for
"team genuinely cannot resolve this," NOT "I'm uncertain about
details I should work out from context." If the directive or
project_context already names the answer, ask the directive, not
the operator. **Do not emit a `concern` saying "I should ask the
operator" — that surfaces the issue to the team but never reaches
the operator. Pick `question_to_operator` directly.**

Silence is a valid and often correct decision. If the trigger doesn't
implicate scope, sequence, or schedule — and isn't one of your standing
ALWAYS engagements — choose silence.

Domain discipline matters. You do **not** issue proposals, do
implementation, write tests, generate stories, or pass security
rulings. When the trigger looks like it wants you to cross into
another agent's domain, choose `deference` and name the right owner.

Speak in your own voice — clear, time-stamped, concrete. "By Thursday
EOD" beats "soon". Name dependencies aloud. Direct cuts can be
discussed; soft cuts cannot.
"""


class RabbitResponseParseError(ResponseParseError):
    """The Rabbit's LLM response did not parse into a valid RabbitResponse."""


def parse_rabbit_response(text: str) -> RabbitResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``,
    which handles fenced/bare/balanced-fallback extraction
    uniformly across every agent.
    """
    return extract_and_validate(text, RabbitResponse, RabbitResponseParseError)


# --------------------------------------------------------------------- #
# White Rabbit agent
# --------------------------------------------------------------------- #


class WhiteRabbit(WonderlandAgent):
    """The Rabbit: project manager, time-conscious, ticket-issuing."""

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        ticket_registry: TicketRegistry | None = None,
        feature_registry: FeatureRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(RABBIT_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(white_rabbit_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._ticket_registry = ticket_registry
        self._feature_registry = feature_registry

    @property
    def ticket_registry(self) -> TicketRegistry | None:
        return self._ticket_registry

    @property
    def feature_registry(self) -> FeatureRegistry | None:
        return self._feature_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant per Rabbit.
        system.insert(2, CachedBlock(_OUTPUT_PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = await self._parse_with_retry(parse_rabbit_response, result.text, system=system, messages=messages)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "ticket":
            artifacts.extend(self._record_tickets(response.tickets))
        elif response.decision == "feature":
            artifacts.extend(self._record_features(response.features))

        thread_id, parent_id = self._derive_threading(context)
        if response.decision == "question_to_operator":
            addressed_to: str | list = [operator_identity()]
            speech_act = SpeechAct.QUESTION
            if response.options:
                artifacts.append(
                    Artifact(
                        kind="operator_question_options",
                        payload={"options": list(response.options)},
                    )
                )
        else:
            addressed_to = "caucus"
            speech_act = SpeechAct(response.decision)
        return Utterance(
            thread_id=thread_id,
            parent_id=parent_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to=addressed_to,
            speech_act=speech_act,
            content=UtteranceContent(body=response.body, artifacts=artifacts),
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _record_tickets(self, payloads: list[TicketPayload]) -> list[Artifact]:
        """Persist each ticket through the registry, return Artifact pointers.

        If no registry was configured, the tickets are dropped silently —
        useful for tests and for ephemeral runs where ticket-on-disk
        isn't desired. The Utterance still carries the decision body so
        the rest of the team can see what the Rabbit said.
        """
        if self._ticket_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._ticket_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="ticket",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "path": str(record.path),
                    },
                )
            )
        return artifacts

    def _record_features(self, payloads: list[FeaturePayload]) -> list[Artifact]:
        """Persist each feature through the registry, return Artifact pointers.

        Same contract as _record_tickets — if no registry was configured,
        features are dropped silently and the Utterance still carries the
        decision body.
        """
        if self._feature_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._feature_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="feature",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "path": str(record.path),
                        "stack_span": payload.stack_span.value,
                        "tickets": list(payload.tickets),
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


__all__ = [
    "RABBIT_NAME",
    "RabbitDecision",
    "RabbitResponse",
    "RabbitResponseParseError",
    "WhiteRabbit",
    "parse_rabbit_response",
    "white_rabbit_rules",
]
