"""Caterpillar — Senior Engineer / Code Review.

Per caterpillar.md and WONDERLAND_SPEC §5. The Caterpillar reads code
slowly. His characteristic move is "Whooo are you?" — pointed at the
code itself: what does it claim to do, what does it actually do, what
will it do six months from now? His characteristic artifact is the
Review with structured per-finding severity, and on the *accept*
verdict he is required to name what was well done — Caterpillar
approval is not given cheaply (§I).

Runtime shape mirrors Cat / Rabbit / Alice / Hatter: load constitution,
wire engagement rules from §III, override deliberate() with a JSON
output protocol. **Reviews are inline-by-default**: the structured
content rides on the bus as an Artifact regardless of whether a
ReviewRegistry was injected. Persistence is opt-in.
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
    any_of,
    body_contains_any,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.review import ReviewPayload, ReviewRegistry
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


CATERPILLAR_NAME = "caterpillar"


# --------------------------------------------------------------------- #
# Engagement rules — caterpillar.md §III as data
# --------------------------------------------------------------------- #


def caterpillar_rules() -> EngagementRules:
    """The Caterpillar's §III engagement policy as machine-checkable rules.

    The Caterpillar listens broadly to anything that touches code or
    code-quality, but his speak surface is narrow — he reviews when
    implementations land and otherwise stays on the mushroom. The
    LLM filter inside ``deliberate()`` does the §III "selectively"
    refinement; the rules here are the coarse first pass.
    """
    quality_words = body_contains_any(
        "quality",
        "maintainability",
        "tests",
        "test coverage",
        "clarity",
        "naming",
        "complexity",
        "convention",
        "review",
    )
    is_tweedle = any_of(speaker_is("tweedledee"), speaker_is("tweedledum"))

    return EngagementRules.of(
        # ALWAYS
        always(SpeechAct.IMPLEMENTATION, condition=is_tweedle),
        always(SpeechAct.REVIEW, condition=addressed_to(CATERPILLAR_NAME)),
        always(SpeechAct.CONCERN, condition=quality_words),
        always(SpeechAct.TEST_SCENARIO, condition=speaker_is("mad_hatter")),
        always(SpeechAct.QUESTION, condition=addressed_to(CATERPILLAR_NAME)),
        # SELECTIVELY — speaker matches; deliberate() decides whether to act
        selectively(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat")),
        selectively(SpeechAct.TICKET, condition=speaker_is("white_rabbit")),
        selectively(SpeechAct.RULING, condition=speaker_is("queen_of_hearts")),
        selectively(SpeechAct.OBSERVATION, condition=speaker_is("dormouse")),
        # RARELY — deference between others isn't his to act on
        rarely(SpeechAct.DEFERENCE),
        # ALMOST_NEVER — explicit guards. The Caterpillar does not issue
        # most things; engaging with same-typed utterances from non-canonical
        # speakers would just be domain-leak noise.
        almost_never(SpeechAct.STORY),
        almost_never(SpeechAct.PROPOSAL),  # not from Cat
        almost_never(SpeechAct.IMPLEMENTATION),  # not from a Tweedle
        almost_never(SpeechAct.TEST_SCENARIO),  # not from Hatter
    )


# --------------------------------------------------------------------- #
# LLM output protocol
# --------------------------------------------------------------------- #


CaterpillarDecision = Literal["review", "concern", "question", "deference", "silence"]


class CaterpillarResponse(BaseModel):
    """Structured JSON the Caterpillar returns from deliberate().

    When ``decision == "review"``, ``reviews`` must contain at least
    one ``ReviewPayload``. The default is one — the Caterpillar's
    pace is one careful read at a time — but the schema permits more
    so a single trigger that batches multiple implementations can be
    handled in one turn if needed.
    """

    decision: CaterpillarDecision
    body: str = ""
    reviews: list[ReviewPayload] = Field(default_factory=list)

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # Live Haiku 4.5 sometimes emits explicit nulls instead of omitting
        # fields — coerce to default per the established pattern.
        return "" if v is None else v

    @field_validator("reviews", mode="before")
    @classmethod
    def _reviews_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "review" and not self.reviews:
            raise ValueError(
                "CaterpillarResponse: decision='review' requires at least one "
                "review in `reviews`. Choose a different decision (concern/"
                "question/etc.) or include the review you intended to issue."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "review" | "concern" | "question" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "reviews": [                        // include ONLY when decision is "review"
    {
      "title": "short human-readable summary, e.g. 'Payment refund handler'",
      "target_utterance_id": "the id of the implementation utterance under review",
      "verdict": "accept" | "request-changes" | "block",
      "findings": [
        {
          "severity": "block" | "change-required" | "suggestion" | "note",
          "title": "noun phrase naming what is wrong",
          "location": "file.py:42 (or file.py:42-58 for a range)",
          "quote": "the offending text, pasted verbatim",
          "read": "your understanding of what this code does, in your own words",
          "concern": "what is wrong, specifically, and why it matters",
          "request": "what would resolve this — actionable, not vibes"
        }
      ],
      "approvals": [
        "things that were notable for being well done — brief but specific"
      ],
      "cross_domain_references": [
        "this implies an architectural question about X — flag for Cat",
        "this implies a missing test scenario for Y — flag for Hatter"
      ]
    }
  ]
}
```

Severity vocabulary is precise:

- `block` — code cannot ship in this state; correctness, security, or invariant violation
- `change-required` — code is acceptable in shape but a specific issue must be addressed before merge
- `suggestion` — would be better with this change, but the author may decline with reasoning
- `note` — observation that does not require action, recorded for the author's awareness

Verdict ↔ findings ↔ approvals must agree:

- `verdict='accept'` requires at least one substantive entry in `approvals`.
  This is non-negotiable. Caterpillar approval is not given cheaply (§I).
  An accept with empty approvals is rubber-stamping — the §VIII failure
  mode this rule exists to prevent. Either name what was well done
  specifically, or choose a different verdict.
- `verdict='request-changes'` requires at least one finding (the author
  needs something specific to act on).
- `verdict='block'` requires at least one finding *with severity='block'*.
  A "block" verdict whose findings are all suggestions is incoherent.

Domain discipline matters. You do **not** propose architecture (the Cat's
domain), write implementations (the Tweedles' domain), or generate test
scenarios (the Hatter's domain). When a finding implies another agent's
domain, use `cross_domain_references` rather than crossing the line
yourself — keep your discovery in code-review territory while pointing
at where the remedy lives. Choose `deference` when the trigger genuinely
belongs to another agent and produces no review for you.

Speak in your own voice — deliberate, precise, direct without harshness.
"This name is misleading because it implies validation when the function
also writes to the database" is a Caterpillar sentence. "Bad name" is
not. Quote the code in findings. Explain the *why* of every request
without lecturing. Celebrate genuinely good code clearly when you see
it; the absence of cheap approval is what makes the substantive approval
mean something. The §VIII guards (rubber-stamping, bikeshedding,
severity inflation, pedantry, architectural drift, author-shaming,
reviewer-as-author trap) are part of who you are; don't slip into them.
"""


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class CaterpillarResponseParseError(ValueError):
    """The Caterpillar's LLM response did not parse into a valid CaterpillarResponse."""


def parse_caterpillar_response(text: str) -> CaterpillarResponse:
    """Extract the fenced JSON block from `text` and validate it."""
    match = _JSON_BLOCK.search(text)
    if match is None:
        candidate = text.strip()
        if not (candidate.startswith("{") and candidate.endswith("}")):
            raise CaterpillarResponseParseError(
                "no JSON block found in Caterpillar response"
            )
        raw = candidate
    else:
        raw = match.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CaterpillarResponseParseError(
            f"Caterpillar response was not valid JSON: {exc}"
        ) from exc
    try:
        return CaterpillarResponse.model_validate(data)
    except ValidationError as exc:
        raise CaterpillarResponseParseError(
            f"Caterpillar response failed schema validation: {exc}"
        ) from exc


# --------------------------------------------------------------------- #
# Caterpillar agent
# --------------------------------------------------------------------- #


class Caterpillar(WonderlandAgent):
    """The Caterpillar: senior engineer, code reviewer, slow on purpose."""

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        review_registry: ReviewRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(CATERPILLAR_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(caterpillar_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._review_registry = review_registry

    @property
    def review_registry(self) -> ReviewRegistry | None:
        return self._review_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant
        # per Caterpillar.
        system.insert(1, CachedBlock(_OUTPUT_PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = parse_caterpillar_response(result.text)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "review":
            artifacts.extend(self._record_reviews(response.reviews))

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

    def _record_reviews(self, payloads: list[ReviewPayload]) -> list[Artifact]:
        """Build artifacts for the review payloads.

        With a registry: persist each review and return file pointers.
        Without a registry: inline the full structured review into the
        Artifact payload, so downstream consumers still have the data
        even though it doesn't live on disk.
        """
        artifacts: list[Artifact] = []
        for payload in payloads:
            if self._review_registry is None:
                artifacts.append(
                    Artifact(
                        kind="review",
                        payload={
                            "title": payload.title,
                            "target_utterance_id": payload.target_utterance_id,
                            "verdict": payload.verdict.value,
                            "review": payload.model_dump(mode="json"),
                        },
                    )
                )
                continue
            record = self._review_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="review",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "verdict": record.verdict.value,
                        "target_utterance_id": record.target_utterance_id,
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
    "CATERPILLAR_NAME",
    "Caterpillar",
    "CaterpillarDecision",
    "CaterpillarResponse",
    "CaterpillarResponseParseError",
    "caterpillar_rules",
    "parse_caterpillar_response",
]
