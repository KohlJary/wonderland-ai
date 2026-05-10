"""Mad Hatter — QA / Testing. Sideways thinking, scenarios over assertions.

Per mad_hatter.md and WONDERLAND_SPEC §5. The Hatter generates test
scenarios from edges and seams; his characteristic move is the
sideways question that exposes a failure mode the team wasn't
watching. Every scenario carries a triaged severity — untriaged
severity is one of the failure modes his constitution actively names
(§VIII).

Runtime shape mirrors Cat / Rabbit / Alice: load constitution, wire
engagement rules from §III, override deliberate() with a JSON output
protocol, persist scenarios through a TestScenarioRegistry. A single
Hatter turn can produce multiple scenarios because edges cluster.
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
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.parsing import ResponseParseError, extract_and_validate
from wonderland.test_scenario import TestScenarioPayload, TestScenarioRegistry
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


HATTER_NAME = "mad_hatter"


# --------------------------------------------------------------------- #
# Engagement rules — mad_hatter.md §III as data
# --------------------------------------------------------------------- #


def mad_hatter_rules() -> EngagementRules:
    """The Hatter's §III engagement policy as machine-checkable rules.

    The Hatter "listens to almost everything" per §III — the rules
    encode that disposition. Heuristics for the conditional engagements
    lean permissive, because deliberate() has the LLM behind it and
    can fall back to silence when the trigger doesn't actually invite
    a scenario.
    """
    is_tweedle = any_of(speaker_is("tweedledee"), speaker_is("tweedledum"))

    return EngagementRules.of(
        # ALWAYS — INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(HATTER_NAME)),
        # ALWAYS
        always(SpeechAct.DIRECTIVE),
        always(SpeechAct.STORY, condition=speaker_is("alice")),
        always(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat")),
        always(SpeechAct.IMPLEMENTATION, condition=is_tweedle),
        always(SpeechAct.CONCERN),
        always(SpeechAct.QUESTION, condition=addressed_to(HATTER_NAME)),
        # SELECTIVELY — speaker matches; deliberate() decides whether to act
        selectively(SpeechAct.TICKET, condition=speaker_is("white_rabbit")),
        selectively(SpeechAct.REVIEW, condition=speaker_is("caterpillar")),
        selectively(SpeechAct.RULING, condition=speaker_is("queen_of_hearts")),
        selectively(SpeechAct.OBSERVATION, condition=speaker_is("dormouse")),
        # RARELY — deference between others isn't his to act on
        rarely(SpeechAct.DEFERENCE),
        # ALMOST_NEVER — explicit guardrails against the §VIII failure modes.
        # The Hatter does not issue stories/tickets/proposals/etc., and
        # echoing one back would just be domain-leak noise.
        almost_never(SpeechAct.STORY),  # not from Alice
        almost_never(SpeechAct.TICKET),  # not from Rabbit
        almost_never(SpeechAct.PROPOSAL),  # not from Cat
    )


# --------------------------------------------------------------------- #
# LLM output protocol
# --------------------------------------------------------------------- #


HatterDecision = Literal[
    "test_scenario",
    "concern",
    "question",
    "question_to_operator",
    "observation",
    "deference",
    "silence",
]


class HatterResponse(BaseModel):
    """Structured JSON the Hatter returns from deliberate().

    When ``decision == "test_scenario"``, ``scenarios`` must contain at
    least one ``TestScenarioPayload`` — a scenario decision without
    scenarios is incoherent. The Hatter may produce multiple scenarios
    per turn because edges cluster around a feature.
    """

    decision: HatterDecision
    body: str = ""
    scenarios: list[TestScenarioPayload] = Field(default_factory=list)

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # The LLM occasionally emits explicit nulls for omitted fields
        # (especially on `silence`). Coerce to default.
        return "" if v is None else v

    @field_validator("scenarios", mode="before")
    @classmethod
    def _scenarios_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "test_scenario" and not self.scenarios:
            raise ValueError(
                "HatterResponse: decision='test_scenario' requires at least one "
                "scenario in `scenarios`. Choose a different decision (concern/"
                "question/etc.) or include the scenarios you intended to issue."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "test_scenario" | "concern" | "question" |
              "question_to_operator" | "observation" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "scenarios": [                      // include ONLY when decision is "test_scenario"
    {
      "title": "vivid, specific title — 'what happens when a user pastes 40,000 emoji', not 'long-input boundary case'",
      "severity": "breakage" | "silent-wrongness" | "degradation" | "curiosity" | "delight",
      "setup": "the state of the world before the interesting moment — be specific",
      "trigger": "the action or event that pokes the system",
      "expected": "what should happen if the system is correct",
      "concern": "your hypothesis about what *will* happen, and why. Required even when you feel confident.",
      "property": "(optional) the general statement this scenario is a witness to, in property-based form when possible",
      "implies": [                    // optional cross-domain handoffs
        "Implies architectural decision about X — flag for Cat.",
        "Implies missed persona Y — flag for Alice."
      ]
    }
  ]
}
```

Severity vocabulary is precise and matters:

- `breakage` — system stops working
- `silent-wrongness` — system appears to work but produces wrong output (most dangerous)
- `degradation` — system works but worse than promised
- `curiosity` — interesting but unlikely to bite
- `delight` — I just want to know what happens

Untriaged severity is a failure mode (§VIII). Severity inflation is
also a failure mode — labeling degradation as breakage to get attention
erodes the signal value of the labels. **Underclaim if anything.**

**`question_to_operator` — escalate to the human operator.** Use
when the team needs a decision only the operator can make: a story
underspecifies what "correctness" means and contracts can't fill
the gap, a scenario surfaces a behavior the operator must confirm
(crash vs degrade, fail-fast vs retry), scope on a test scenario
the team can't agree on. The framework pauses the meeting,
surfaces your question, and resumes when the operator replies
(their answer arrives as an OBSERVATION on the bus). Body should
be ONE specific question — not a paragraph of options — so the
operator can answer in one or two sentences. Reserve for "team
genuinely cannot resolve this," NOT "I'm uncertain about an edge
case I should explore in a `delight`-severity scenario." If the
directive or project_context already names the answer, ask the
directive, not the operator. **Do not emit a `concern` saying "I
should ask the operator" — that surfaces the issue to the team
but never reaches the operator. Pick `question_to_operator`
directly.**

Silence is a valid and often correct decision. The §VI quiescence rule:
once your scenarios for a thread have been triaged and the high-severity
ones have either become tests or been explicitly accepted as known
risks, you fall back to listening. Re-engage when implementation
arrives, when production telemetry contradicts assumptions, or when a
new persona enters the conversation. Don't pad threads after settlement.

Domain discipline matters. You do **not** propose architecture, write
tickets, write stories, or pass rulings. When the trigger looks like it
wants you to cross into another agent's domain, the right move is
usually a `test_scenario` whose `implies` field flags the cross-domain
implication for the right owner — keep your discovery in QA territory
while pointing at where the remedy lives. `deference` is the right call
when the trigger genuinely belongs to another agent and produces no
scenario for you.

Speak in your own voice — concrete, vivid, cheerful. "What happens when
a user pastes 40,000 emoji" is a Hatter sentence. "Boundary value
analysis on input length" is a sentence written by someone who has lost
the thread. The work is genuinely funny because the universe's edges
are genuinely funny; let that show. Hostility is a failure mode (§VIII)
— the warmth toward the Tweedles is part of how QA gets done.
"""


_TOOLS_SECTION = """
**Tools available.** You can call `read_file`, `list_files`, `grep`,
and `write_file` to ground test scenarios in the actual code AND to
ship real test files alongside your scenarios.

- `read_file` and `grep`: read the implementation a Tweedle just shipped
  before naming the scenarios it has to handle. A scenario that names
  a specific function and a concrete input that breaks it is sharper
  than a scenario named in the abstract.
- `list_files`: see the existing test layout before adding new files.
- `write_file`: write actual pytest files when a scenario is concrete
  enough to express in code. Convention: tests under `tests/` mirror
  the source path (`tests/test_foo.py` for `src/foo.py`). Each test
  function name includes the failure mode in plain English (e.g.,
  `test_handler_returns_timeout_when_translator_takes_too_long`).
  Only write the test when you can make it fail meaningfully on a
  bug; speculative tests for code that isn't shipped yet should
  remain scenario-shaped (markdown).

You do not write source code (the Tweedles' domain) or implementations
of features (the Tweedles' too). Tests that exercise the Tweedles'
implementations are your domain — that's the natural extension of the
test scenario into executable form.
"""


_OUTPUT_PROTOCOL_WITH_TOOLS = _OUTPUT_PROTOCOL + _TOOLS_SECTION


class HatterResponseParseError(ResponseParseError):
    """The Hatter's LLM response did not parse into a valid HatterResponse."""


def parse_hatter_response(text: str) -> HatterResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``,
    which handles fenced/bare/balanced-fallback extraction
    uniformly across every agent.
    """
    return extract_and_validate(text, HatterResponse, HatterResponseParseError)


# --------------------------------------------------------------------- #
# Mad Hatter agent
# --------------------------------------------------------------------- #


class MadHatter(WonderlandAgent):
    """The Mad Hatter: QA, edge-finder, scenario-issuer, severity-triaging."""

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        test_scenario_registry: TestScenarioRegistry | None = None,
        tools=None,  # type: ignore[no-untyped-def]
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(HATTER_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(mad_hatter_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._test_scenario_registry = test_scenario_registry
        self._tools = tools

    @property
    def test_scenario_registry(self) -> TestScenarioRegistry | None:
        return self._test_scenario_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant per
        # Hatter. With-tools variant when tools are wired so the LLM is told
        # about the read/list/grep + write_file (for actual test files)
        # capabilities.
        protocol = _OUTPUT_PROTOCOL_WITH_TOOLS if self._tools is not None else _OUTPUT_PROTOCOL
        system.insert(2, CachedBlock(protocol))

        if self._tools is not None:
            response_text = await self._complete_with_tools(system, messages)
        else:
            result = await self.llm.complete(system=system, messages=messages)
            response_text = result.text
        response = await self._parse_with_retry(parse_hatter_response, response_text, system=system, messages=messages)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "test_scenario":
            artifacts.extend(self._record_scenarios(response.scenarios))

        thread_id, parent_id = self._derive_threading(context)
        if response.decision == "question_to_operator":
            addressed_to: str | list = [operator_identity()]
            speech_act = SpeechAct.QUESTION
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

    def _record_scenarios(self, payloads: list[TestScenarioPayload]) -> list[Artifact]:
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
                        "severity": record.severity.value,
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
    "HATTER_NAME",
    "HatterDecision",
    "HatterResponse",
    "HatterResponseParseError",
    "MadHatter",
    "mad_hatter_rules",
    "parse_hatter_response",
]
