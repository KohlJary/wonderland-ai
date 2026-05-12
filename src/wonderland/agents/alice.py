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
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.parsing import ResponseParseError, extract_and_validate
from wonderland.story import StoryPayload, StoryRegistry
from wonderland.test_scenario import (
    TestScenarioPayload,
    TestScenarioRegistry,
)
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
        # ALWAYS — INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(ALICE_NAME)),
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


AliceDecision = Literal[
    "story",
    "test_scenario",
    "concern",
    "question",
    "question_to_operator",
    "reframe",
    "deference",
    "silence",
]


class AliceResponse(BaseModel):
    """Structured JSON Alice returns from deliberate().

    When ``decision == "story"``, ``stories`` must contain at least
    one ``StoryPayload`` — a story decision without stories is
    nonsense. Alice may produce multiple stories per turn because
    she's inhabiting multiple personas in succession.

    When ``decision == "test_scenario"``, ``scenarios`` must contain
    at least one ``TestScenarioPayload`` — the tea-party (M6)
    extension where Alice writes happy-path scenarios from her
    persona's POV instead of polluting the story pool with
    test-shaped stories. Hatter still writes the edge / failure
    scenarios; Alice covers the persona-anchored happy paths.
    """

    decision: AliceDecision
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
    stories: list[StoryPayload] = Field(default_factory=list)
    scenarios: list[TestScenarioPayload] = Field(default_factory=list)

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # The LLM occasionally emits explicit nulls for omitted fields
        # (especially on `silence`). Coerce to default — schema intent and
        # absent-field intent are the same here.
        return "" if v is None else v

    @field_validator("stories", mode="before")
    @classmethod
    def _stories_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    @field_validator("scenarios", mode="before")
    @classmethod
    def _scenarios_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "story" and not self.stories:
            raise ValueError(
                "AliceResponse: decision='story' requires at least one story "
                "in `stories`. Choose a different decision (concern/question/etc.) "
                "or include the stories you intended to issue."
            )
        if self.decision == "test_scenario" and not self.scenarios:
            raise ValueError(
                "AliceResponse: decision='test_scenario' requires at least "
                "one scenario in `scenarios`. Choose a different decision "
                "or include the scenarios you intended to issue."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "story" | "test_scenario" | "concern" | "question" |
              "question_to_operator" | "reframe" | "deference" | "silence",
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
  ],
  "scenarios": [                      // include ONLY when decision is "test_scenario"
    {
      "title": "vivid, specific title from your persona's POV — 'Maya pastes a translated reply over the original draft', not 'happy-path translation flow'",
      "severity": "breakage" | "silent-wrongness" | "degradation" | "curiosity" | "delight",
      "setup": "the state of the world before the persona acts — be specific to the persona",
      "trigger": "the persona's action that the system has to handle correctly",
      "expected": "what the persona expects to see, in their own terms",
      "concern": "why this scenario matters from a user-need POV — 'if this breaks, Maya can't tell that her translation landed'",
      "property": "(optional) the general statement this scenario witnesses",
      "implies": []
    }
  ]
}
```

**`test_scenario` — Alice's tea-party (M6) move.** When you're in
the tea party with the Mad Hatter, your job is NOT to add stories;
the story pool is already shipped. Your job is to write happy-path
test scenarios from your persona's POV — "Maya pastes a 200-char
draft and expects the translated reply within 2s" — while the
Hatter covers the edges. Severity for happy-path scenarios is
typically `silent-wrongness` (the system appears to work but
returns the wrong thing for the persona) or `degradation` (the
system is slower than the persona would tolerate). Use this
decision ONLY in tea-party threads where Hatter has been seeded
as a co-roster; everywhere else, story is your shape.

**`question_to_operator` — escalate to the human operator.** Use when
the team needs a decision only the operator can make: stack
constraints contradicting the directive, business priority calls,
UX preferences that can't be inferred from stories. The framework
pauses the meeting, surfaces your question to the operator, and
resumes when they reply (their answer arrives as an OBSERVATION on
the bus, visible to the whole team). Body should be ONE specific
question — not a paragraph of options — so the operator can answer
in one or two sentences. Reserve for "team genuinely cannot
resolve this," NOT "I'm uncertain about details I should work out
from context." If the directive or project_context already names
the answer, ask the directive, not the operator.

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


class AliceResponseParseError(ResponseParseError):
    """Alice's LLM response did not parse into a valid AliceResponse."""


def parse_alice_response(text: str) -> AliceResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``, which
    handles fenced/bare/balanced-fallback extraction uniformly across
    every agent.
    """
    return extract_and_validate(text, AliceResponse, AliceResponseParseError)


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
        test_scenario_registry: TestScenarioRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(ALICE_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(alice_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._story_registry = story_registry
        self._test_scenario_registry = test_scenario_registry

    @property
    def story_registry(self) -> StoryRegistry | None:
        return self._story_registry

    @property
    def test_scenario_registry(self) -> TestScenarioRegistry | None:
        return self._test_scenario_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant per Alice.
        system.insert(2, CachedBlock(_OUTPUT_PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = await self._parse_with_retry(parse_alice_response, result.text, system=system, messages=messages)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "story":
            artifacts.extend(self._record_stories(response.stories))
        elif response.decision == "test_scenario":
            artifacts.extend(
                self._record_test_scenarios(response.scenarios)
            )

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

    def _record_test_scenarios(
        self, payloads: list[TestScenarioPayload]
    ) -> list[Artifact]:
        """Mirror of ``_record_stories`` for the tea-party (M6) shape
        where Alice writes persona-anchored happy-path scenarios.
        Same on-disk shape as Hatter's scenarios; the substrate
        treats them as test_scenario artifacts regardless of speaker
        so M7 sees both alongside each other when iterating per
        ticket.
        """
        if self._test_scenario_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._test_scenario_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="test_scenario",
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
