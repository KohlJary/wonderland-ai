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
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.parsing import ResponseParseError, extract_and_validate
from wonderland.review import ReviewPayload, ReviewRegistry
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
        # ALWAYS — INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(CATERPILLAR_NAME)),
        # ALWAYS — meeting frame from Dodo (or any convenor). Without
        # this, review-only meetings (Caterpillar + Tweedles, no fresh
        # IMPLEMENTATION from sibling because the implementation was a
        # prior-thread seed) don't engage on the convenor directive:
        # the directive lands on the bus and Caterpillar stays silent
        # because his other triggers (IMPLEMENTATION from Tweedles,
        # REVIEW addressed to him) haven't fired. The directive is what
        # tells him to call git_status / git_diff and surface findings.
        always(SpeechAct.DIRECTIVE),
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


CaterpillarDecision = Literal[
    "review",
    "concern",
    "question",
    "question_to_operator",
    "deference",
    "silence",
]


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
  "decision": "review" | "concern" | "question" | "question_to_operator" |
              "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "reviews": [                        // include ONLY when decision is "review"
    {
      "title": "short human-readable summary, e.g. 'Payment refund handler'",
      "target_files": ["src/foo.py", "src/bar.ts"],  // the files this review covers
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

**The working tree IS the implementation artifact.** Earlier protocols
expected an `implementation` utterance on the bus to anchor your
review, but the framework now treats files-on-disk as the deliverable
directly. Your starting move on a review thread is `git_status`, then
`git_diff` for any path that changed. Each review's `target_files`
names the paths your review covers — pulled from what you read in
the diff, not from a parallel metadata utterance. Findings cite
file:line locations within those paths.

When the directive opens a review thread (or any thread you're
engaged on), the decision tree is:

1. Call `git_status`. If the working tree is clean (no changes since
   the prior commit), there is nothing to review — choose `silence`.
2. If there are changes, call `git_diff` (or `git_diff path` to
   narrow). Read the actual code.
3. Ship a `review` with `target_files` listing what you read,
   `verdict` matching your judgment, and `findings` for anything
   you'd request changes on. An empty findings list with verdict
   `accept` is allowed (and common!) — but it requires substantive
   `approvals`, per the rule below.

Choosing `deference` because "the implementation utterance isn't on
the bus" is the failure mode this protocol revision exists to
prevent. The diff IS the work; the diff is enough to review.

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


_TOOLS_SECTION = """
**Tools available.** The working tree IS the implementation artifact.
Reach for `git_status` first to see what the meeting produced, then
`git_diff` to read the changes — that is how you find what shipped,
not by consulting separate metadata.

- **`git_status`**: lists files modified, added, deleted, or
  untracked since the last commit. Your starting move. Tells you
  the surface area of work to review.
- **`git_diff`** (no path): full unified diff of working-tree
  changes against HEAD. With a `path` argument: scoped to one file.
  Use scoped diffs when the full diff is large.
- **`read_file`**: full file contents (post-change). Use when a
  finding needs the surrounding context, or when the diff
  references a function whose definition you need to see in full.
- **`list_files`**: explore the project shape — what other files
  exist that the change might affect.
- **`grep`**: when you suspect duplication or drift, search for
  the relevant symbol or contract version across the tree.

A finding that names a specific file and line is sharper than a
finding that names a pattern. Quote the code; cite the diff.

`write_file` is also available, but you do not write source code —
that is the Tweedles' domain. The review is your characteristic
artifact, persisted by the framework when you choose
`decision: "review"`. If you find yourself wanting to write a
patch, surface it as a `finding` with a concrete recommendation
rather than implementing the fix yourself; that's the
reviewer-as-author trap your §VIII names. The one legitimate write
is to documentation files when a finding implies a doc gap — and
even then, prefer flagging the gap as a finding.
"""


_OUTPUT_PROTOCOL_WITH_TOOLS = _OUTPUT_PROTOCOL + _TOOLS_SECTION


class CaterpillarResponseParseError(ResponseParseError):
    """The Caterpillar's LLM response did not parse into a valid CaterpillarResponse."""


def parse_caterpillar_response(text: str) -> CaterpillarResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``, which
    handles fenced/bare/balanced-fallback extraction uniformly across
    every agent.
    """
    return extract_and_validate(text, CaterpillarResponse, CaterpillarResponseParseError)


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
        tools=None,  # type: ignore[no-untyped-def]
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(CATERPILLAR_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(caterpillar_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._review_registry = review_registry
        self._tools = tools

    @property
    def review_registry(self) -> ReviewRegistry | None:
        return self._review_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant
        # per Caterpillar. With-tools variant when tools are wired so the
        # LLM is told about the read/list/grep capabilities.
        protocol = _OUTPUT_PROTOCOL_WITH_TOOLS if self._tools is not None else _OUTPUT_PROTOCOL
        system.insert(2, CachedBlock(protocol))

        if self._tools is not None:
            response_text = await self._complete_with_tools(system, messages)
        else:
            result = await self.llm.complete(system=system, messages=messages)
            response_text = result.text
        response = await self._parse_with_retry(parse_caterpillar_response, response_text, system=system, messages=messages)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "review":
            artifacts.extend(self._record_reviews(response.reviews))

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
                            "target_files": list(payload.target_files),
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
                        "target_files": list(record.target_files),
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
