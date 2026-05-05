"""Alice — User / Product Owner. She inhabits users.

Per alice.md and WONDERLAND_SPEC §5. Alice's characteristic move is
the naive question that exposes assumption; her characteristic
artifact is the user story written from an inhabited persona. She
opens most threads — the team's work cascades from her stories.

Runtime shape mirrors CheshireCat / WhiteRabbit: load constitution,
wire engagement rules from §III, override deliberate() with a JSON
output protocol, persist stories through the T21 StoryRegistry. A
single Alice turn can produce multiple stories because she's
inhabiting multiple personas in succession.
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
    addressed_to,
    almost_never,
    always,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.story import StoryPayload, StoryRegistry
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


ALICE_NAME = "alice"


# --------------------------------------------------------------------- #
# Engagement rules — alice.md §III as data
# --------------------------------------------------------------------- #


def alice_rules() -> EngagementRules:
    """Alice's §III engagement policy as machine-checkable rules.

    Engagement leans permissive for speaker-matched cases (Cat,
    Rabbit, Hatter, etc.) — the constitutional refinement ("only when
    UX implication" / "only when drift from stories") happens in
    deliberate(), where Alice has the full LLM behind her. Same
    disposition as the Cat and Rabbit: when in doubt, engage and
    choose silence.
    """
    return EngagementRules.of(
        # ALWAYS — Alice opens threads and reacts to specific signals
        always(SpeechAct.DIRECTIVE),
        always(SpeechAct.QUESTION, condition=addressed_to(ALICE_NAME)),
        always(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat")),
        always(SpeechAct.TICKET, condition=speaker_is("white_rabbit")),
        always(SpeechAct.TEST_SCENARIO, condition=speaker_is("mad_hatter")),
        # SELECTIVELY — speaker matches; deliberate() decides whether to act
        selectively(SpeechAct.IMPLEMENTATION),
        selectively(SpeechAct.REVIEW, condition=speaker_is("caterpillar")),
        selectively(SpeechAct.RULING, condition=speaker_is("queen_of_hearts")),
        selectively(SpeechAct.OBSERVATION, condition=speaker_is("dormouse")),
        # RARELY — explicit per §III
        rarely(SpeechAct.PROPOSAL),  # any non-Cat proposal
        # ALMOST_NEVER — deference between others
        almost_never(SpeechAct.DEFERENCE),
    )


# --------------------------------------------------------------------- #
# LLM output protocol
# --------------------------------------------------------------------- #


AliceDecision = Literal["story", "concern", "question", "reframe", "deference", "silence"]


class AliceResponse(BaseModel):
    """Structured JSON Alice returns from deliberate().

    When ``decision == "story"``, ``stories`` must contain at least
    one ``StoryPayload`` — a story decision without stories is
    nonsense. Alice may produce multiple stories per turn because
    she's inhabiting multiple personas in succession.
    """

    decision: AliceDecision
    body: str = ""
    stories: list[StoryPayload] = Field(default_factory=list)

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "story" and not self.stories:
            raise ValueError(
                "AliceResponse: decision='story' requires at least one story "
                "in `stories`. Choose a different decision (concern/question/etc.) "
                "or include the stories you intended to issue."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "story" | "concern" | "question" | "reframe" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "stories": [                        // include ONLY when decision is "story"
    {
      "title": "short, specific title",
      "persona": "a specific person — name, age range, situation, why they are here. Not 'the user'.",
      "situation": "what is happening in their life when they encounter this part of the system",
      "need": "As [persona], I want [outcome], so that [purpose].",
      "acceptance": [
        "observable, testable condition of done",
        "another condition"
      ],
      "tier": "core" | "enrichment" | "fast-follow",
      "confusion_flags": [
        "things that felt wrong to you as you wrote this, even if you can't fully articulate why",
        "include at least one — stories without flags are suspect (you weren't paying attention, or the story is too easy)"
      ]
    }
  ]
}
```

Silence is a valid and often correct decision. If the trigger does not
implicate user need — or if your story set for this thread is already
shipped and the team is working from it correctly — choose silence.
The product-owner-who-keeps-adding-stories-during-implementation is a
known failure mode; you guard against it.

Domain discipline matters. You do **not** issue tickets, propose
architecture, write tests, or specify implementation. When the trigger
looks like it wants you to cross into another agent's domain, choose
`deference` and name the right owner.

Speak in your own voice — concrete personas, observable conditions.
"As the user, I want X" is suspect; "As Maya, a 31-year-old polyglot
moderator drowning in cross-language threads, I want X" is what stories
look like when they're real.
"""


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class AliceResponseParseError(ValueError):
    """Alice's LLM response did not parse into a valid AliceResponse."""


def parse_alice_response(text: str) -> AliceResponse:
    """Extract the fenced JSON block from `text` and validate it."""
    match = _JSON_BLOCK.search(text)
    if match is None:
        candidate = text.strip()
        if not (candidate.startswith("{") and candidate.endswith("}")):
            raise AliceResponseParseError("no JSON block found in Alice response")
        raw = candidate
    else:
        raw = match.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AliceResponseParseError(f"Alice response was not valid JSON: {exc}") from exc
    try:
        return AliceResponse.model_validate(data)
    except ValidationError as exc:
        raise AliceResponseParseError(f"Alice response failed schema validation: {exc}") from exc


# --------------------------------------------------------------------- #
# Alice agent
# --------------------------------------------------------------------- #


class Alice(WonderlandAgent):
    """Alice: stranger in the system, inhabiting users, naively-question-asking."""

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        story_registry: StoryRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(ALICE_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(alice_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._story_registry = story_registry

    @property
    def story_registry(self) -> StoryRegistry | None:
        return self._story_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant per Alice.
        system.insert(1, CachedBlock(_OUTPUT_PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = parse_alice_response(result.text)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "story":
            artifacts.extend(self._record_stories(response.stories))

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

    def _record_stories(self, payloads: list[StoryPayload]) -> list[Artifact]:
        if self._story_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._story_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="story",
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
    "ALICE_NAME",
    "Alice",
    "AliceDecision",
    "AliceResponse",
    "AliceResponseParseError",
    "alice_rules",
    "parse_alice_response",
]
