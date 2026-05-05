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

import json
import re
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, ValidationError

from wonderland.agent import Context, WonderlandAgent
from wonderland.engagement import (
    EngagementRules,
    almost_never,
    always,
    any_of,
    body_contains_any,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.ticket import TicketPayload, TicketRegistry
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
        # ALWAYS
        always(SpeechAct.DIRECTIVE),
        always(SpeechAct.STORY, condition=speaker_is("alice")),
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


RabbitDecision = Literal["ticket", "concern", "question", "reframe", "deference", "silence"]


class RabbitResponse(BaseModel):
    """Structured JSON the Rabbit returns from deliberate().

    When ``decision == "ticket"``, ``tickets`` must contain at least
    one ``TicketPayload`` — a ticket decision without tickets is
    nonsense. For other decisions, ``tickets`` is ignored.
    """

    decision: RabbitDecision
    body: str = ""
    tickets: list[TicketPayload] = Field(default_factory=list)

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "ticket" and not self.tickets:
            raise ValueError(
                "RabbitResponse: decision='ticket' requires at least one ticket "
                "in `tickets`. Choose a different decision (concern/question/etc.) "
                "or include the tickets you intended to issue."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "ticket" | "concern" | "question" | "reframe" | "deference" | "silence",
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
  ]
}
```

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


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class RabbitResponseParseError(ValueError):
    """The Rabbit's LLM response did not parse into a valid RabbitResponse."""


def parse_rabbit_response(text: str) -> RabbitResponse:
    """Extract the fenced JSON block from `text` and validate it."""
    match = _JSON_BLOCK.search(text)
    if match is None:
        candidate = text.strip()
        if not (candidate.startswith("{") and candidate.endswith("}")):
            raise RabbitResponseParseError("no JSON block found in Rabbit response")
        raw = candidate
    else:
        raw = match.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RabbitResponseParseError(f"Rabbit response was not valid JSON: {exc}") from exc
    try:
        return RabbitResponse.model_validate(data)
    except ValidationError as exc:
        raise RabbitResponseParseError(f"Rabbit response failed schema validation: {exc}") from exc


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
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(RABBIT_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(white_rabbit_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._ticket_registry = ticket_registry

    @property
    def ticket_registry(self) -> TicketRegistry | None:
        return self._ticket_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant per Rabbit.
        system.insert(1, CachedBlock(_OUTPUT_PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = parse_rabbit_response(result.text)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "ticket":
            artifacts.extend(self._record_tickets(response.tickets))

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
