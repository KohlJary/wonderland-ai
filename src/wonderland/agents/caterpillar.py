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
from wonderland.story import StoryPayload, StoryRegistry
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
        # M1 review pass + plumbing-story generation: engage on Alice's
        # stories so deliberate() can produce a concern/question
        # (review the shape) or a story of its own (cover the
        # plumbing surfaces Alice's "inhabit users" frame doesn't
        # reach — testing infra, observability, deployment, etc.).
        always(SpeechAct.STORY),
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
    "story",
    "concern",
    "question",
    "question_to_operator",
    "retract",
    "deference",
    "silence",
]


class RetractionPayload(BaseModel):
    """Payload shape for a single retraction the Caterpillar ships
    when an artifact already on disk (story / feature / etc.) has
    drifted from scope and needs to be removed. P15 T-m7 substrate."""

    target_kind: Literal[
        "story", "feature", "ticket", "adr", "milestone", "requirement"
    ]
    target_slug: str
    reason: str = Field(
        ...,
        description=(
            "One-line scope/coherence note explaining why this "
            "artifact is being walked back. Surfaces in the "
            "ArtifactRetracted observer event."
        ),
    )


class CaterpillarResponse(BaseModel):
    """Structured JSON the Caterpillar returns from deliberate().

    When ``decision == "review"``, ``reviews`` must contain at least
    one ``ReviewPayload``. The default is one — the Caterpillar's
    pace is one careful read at a time — but the schema permits more
    so a single trigger that batches multiple implementations can be
    handled in one turn if needed.

    When ``decision == "story"``, ``stories`` must contain at least
    one ``StoryPayload``. M1 added Caterpillar to the roster (was
    Alice-only) so stories about plumbing — testing infrastructure,
    observability, error-handling, deployment, internal tools — get
    written too. Alice owns user-facing stories; Caterpillar covers
    the developer-as-user / operator-as-user / sysadmin-as-user
    surfaces Alice's "inhabit USERS" framing doesn't reach. Same
    schema (StoryPayload), different persona convention.
    """

    decision: CaterpillarDecision
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
    reviews: list[ReviewPayload] = Field(default_factory=list)
    stories: list[StoryPayload] = Field(default_factory=list)
    retractions: list[RetractionPayload] = Field(default_factory=list)

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
        if self.decision == "retract" and not self.retractions:
            raise ValueError(
                "CaterpillarResponse: decision='retract' requires at least "
                "one entry in `retractions`. Each entry names the "
                "(target_kind, target_slug, reason) of an artifact you are "
                "removing from this run's deliverables."
            )
        if self.decision == "story" and not self.stories:
            raise ValueError(
                "CaterpillarResponse: decision='story' requires at least one "
                "entry in `stories`. Declaring the decision without shipping "
                "the payload was the validation2 pilot's deadlock shape — "
                "agent kept saying 'I will author' without actually authoring. "
                "Choose `silence` or `concern` if you don't have a story to "
                "ship; choose `story` only when the stories[] payload is real."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "review" | "story" | "concern" | "question" |
              "question_to_operator" | "retract" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "retractions": [                    // include ONLY when decision is "retract"
    {
      "target_kind": "story" | "feature" | "ticket" | "adr" | "milestone" | "requirement",
      "target_slug": "the slug of the artifact you are removing — must match a slug already on the bus / on disk in this run",
      "reason": "one-line scope/coherence justification — surfaces in the live-watch + audit log"
    }
  ],
  "stories": [                        // include ONLY when decision is "story"
    {
      "title": "short, specific title",
      "persona": "developer/operator/sysadmin/etc. — name, role, situation, why they need this. Specific, not generic.",
      "situation": "what is happening when they encounter this part of the system",
      "need": "As [persona], I want [outcome], so that [purpose].",
      "acceptance": [
        "observable, testable condition of done",
        "another condition"
      ],
      "tier": "core" | "enrichment" | "fast-follow",
      "confusion_flags": [
        "things that felt wrong as you wrote this — at least one is required"
      ],
      "realizes_requirements": [
        "requirement-slug-this-plumbing-story-addresses (often a `constraint` or `integration` kind from discovery, e.g., 'react-frontend-sqlite-backend-v1-stack-locked')"
      ],
      "milestone": "active milestone slug verbatim from the milestone artifact in your context (e.g. 'm1-foundation-data-layer-api-contract') — REQUIRED when the run is milestone-scoped; null only when no scope is active. Cross-milestone supporting concerns surface as a `concern`, not as a story shared across scopes."
    }
  ],
  "reviews": [                        // include ONLY when decision is "review"
    {
      "title": "short human-readable summary, e.g. 'Payment refund handler'",
      "target_files": ["src/foo.py", "src/bar.ts"],  // the files this review covers
      "verdict": "accept" | "request-changes" | "block",
      "findings": [
        {
          "severity": "block" | "change-required" | "suggestion" | "note",
          "kind": "bug" | "meta" | "convention" | "nit",  // optional; default "bug". See guidance below.
          "title": "noun phrase naming what is wrong",
          "location": "file.py:42 (or file.py:42-58 for a range)",
          "quote": "the offending text, pasted verbatim",
          "read": "your understanding of what this code does, in your own words",
          "concern": "what is wrong, specifically, and why it matters",
          "request": "what would resolve this — actionable, not vibes",
          "test_coverage_required": false  // optional; default FALSE — and false is right for almost every finding. Set true ONLY when the fix introduces a brand-new capability surface that the team never wrote a test against (✅ "add JWT validation," "implement conflict-resolution UX," "introduce retry-with-backoff"). FALSE for correction findings even though no test exists for the bug (❌ schema drift, contract mismatch, missing null check, tz bug, off-by-one, typo, missing migration, OperationalError-class). Heuristic: if a Tweedle could write the test in one sitting without Mad Hatter's adversarial discipline, leave it false. In a typical 5-finding review, 0–1 should be true. When in doubt, false.
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

**Kind is ORTHOGONAL to severity.** Severity answers *"how
concerned should the author be?"* — Kind answers *"should the
substrate spawn implementation work to address this?"*

- `bug` (DEFAULT) — implementation defect; behavior is wrong.
  Spawns a follow-up implementation ticket when severity is
  `block` / `change-required`. Use for: schema drift, contract
  mismatch, missing null check, tz bug, off-by-one, missing
  migration, OperationalError-class, XSS gap, broken endpoint
  semantics, the wrong field name on the response, etc.
- `meta` — meta-feedback about how the code expresses itself;
  behavior is correct but the expression could be clearer.
  Recorded for the author; DOES NOT spawn a follow-up
  implementation ticket regardless of severity. Use for:
  *"test assertions lack failure messages,"* *"this function
  name implies idempotence but the body isn't,"* *"this comment
  contradicts the code,"* *"variable naming inconsistent across
  the module,"* *"the test allows multiple conflicting
  interpretations of the spec."* These are real review feedback
  the author should act on in their next touch — but they're
  NOT bugs that need a fresh M6+M7+M8 cycle.
- `convention` — codebase convention / style. Same shape as
  `meta` (advisory, no ticket spawn). Use for: *"this codebase
  uses snake_case for fields; this struct uses camelCase,"*
  *"error responses elsewhere use a `code` field; this one uses
  `error_code`."*
- `nit` — minor cosmetic. Advisory, no ticket spawn. Use
  sparingly — many nits in one review is bikeshedding (§VIII).

**The bug-vs-meta distinction matters for cost discipline.**
Telemetry from mvp-demo2 (analysis 033 §5.1; M7 cost
decomposition) showed ~30% of M7 spend went to a recursive
test-quality cycle: findings marked `change-required` were
about test clarity, not implementation correctness, but the
substrate didn't know the difference and spawned follow-up
tickets. The Tweedles re-implemented the tests; you reviewed
them again; another meta-feedback finding surfaced; loop. With
`kind: meta` you can say *"this test could be clearer"* with
appropriate severity, the author gets the feedback recorded in
the review artifact, and the substrate does NOT respawn the
expensive M6+M7+M8 cycle. **Use `meta` whenever the underlying
behavior is correct + the finding is about expression.**

In a typical 5-finding review: most findings are `bug`; 1-2
might be `meta` or `convention` if the implementation works
but the code has clarity issues; nits should be rare.

**`location` is load-bearing — split findings by side, never
straddle.** The substrate derives the synthesized follow-up
ticket's `stack_span` (frontend / backend / full-stack) from
your finding's `location` field. Frontend paths
(`*/frontend/*`, `*.tsx`, `*.jsx`, `*.css`) land **only**
Tweedledee in the M7 follow-up. Backend paths
(`*/backend/*`, `*.py`, `*.sql`, `/api/`, `/models.py`,
`/migrations/`) land **only** Tweedledum. **Ambiguous or
multi-side locations fall back to `full-stack`, which loads
BOTH Tweedles and roughly doubles M7 cost for that ticket.**

Default every finding to a single side. Cite ONE file (or
multiple files all on the same side) in `location`. **If a
finding feels cross-cutting, you almost certainly have two
findings, not one:**

- Contract drift where the backend returns `error_code` but
  the frontend expects `code` → TWO findings. One backend
  (rename the response field), one frontend (consume the
  right key). Each gets its own `location`, `concern`, and
  `request`.
- Validation gap where the backend doesn't reject bad input
  AND the frontend doesn't clamp it → TWO findings. One
  server-side, one client-side.
- Logging gap where the backend writes the wrong shape AND
  the frontend silently swallows the error → TWO findings.

Filing a single full-stack finding to cover both sides
hides one of the two specific changes behind a vague joint
description and engages a Tweedle with nothing concrete to
ship — they end up either rubber-stamping or inventing
work. The few cases where a single full-stack finding IS
correct: a directive-level cross-cutting decision that
genuinely cannot be split (e.g. *"the whole app needs to
move from REST polling to WebSocket subscriptions"*).
You should be able to count those on one hand per pilot.

**When in doubt: split.** Two well-scoped single-side
findings beat one vague straddling finding for both review
quality AND downstream M7 cost.

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

**`story` — write a plumbing-side user story.** This is your M1
generative move; you and Alice both write stories at the scoping
meeting. Alice's frame is "inhabit users" — end-user-facing
needs. Your frame is "developer / operator / sysadmin as user" —
the surfaces Alice's framing doesn't reach: testing infrastructure
("As Maya the developer, I want to run the dashboard with
OBOL_MOCK=1 so I can exercise UX without setting up Plaid"),
observability ("As Sam the on-call engineer, I want structured
logs at ERROR severity when sync fails, so I can diagnose
production issues without re-running locally"), error-handling
discipline, deployment ergonomics, internal tools, build
hygiene. Same StoryPayload shape as Alice's stories (persona,
situation, need, acceptance, confusion_flags), different persona
convention. Aim for 1–3 plumbing stories per M1 — fewer than
Alice's 3–6 user stories, since user-facing concerns dominate.
**Don't write user-facing stories yourself** — that's Alice's
domain. If your story's persona is an end user (Jordan checking
balances, Maya tracking invoices), it belongs to Alice; defer.
At meetings other than M1, `story` is rare — use it when you
notice during a review that a missing plumbing story was the
upstream cause of the bug you're flagging.

**Foundation-only milestones invert your ratio.** When the
milestone scope is pure infrastructure — auth substrate, schema
seams, sync layer contracts, provider abstractions, build/deploy
plumbing — Alice has no Marcus-shaped persona to anchor against
and her natural M1 move is `silence` or `concern`. **You become
the primary author** in that context, not the secondary one.
Recognize a foundation-only milestone by:

  - The milestone goal/done_when names systems concerns
    (schema, sync, auth, provider abstraction) rather than user
    flows ("Marcus logs a session", "operator sees progress")
  - The consumes_requirements are mostly ``constraint`` /
    ``integration`` / ``scope`` / ``success_criterion`` kinds
    rather than user-facing needs
  - The seeded personas, when traced into the milestone scope,
    point at developer / operator / installer / sysadmin
    surfaces

In that case ship 3–6 foundation stories yourself with
developer/operator/installer personas — DO NOT wait for Alice
to author and then concern her work. The validation2 pilot
showed this deadlock: Alice tried Marcus stories that didn't
fit, you ``concern``ed them, she retried, repeat. Recovery
took several rotations and consumed budget that should have
shipped the foundation stories directly. The lane is yours;
take it. Alice will support you with `concern` when your
foundation story has a user-facing implication she sees you
missing.

**`retract` — remove an off-scope artifact already on disk.** The
substrate gave you this primitive in P15 T-m7 because `concern`
names a violation without correcting it — and once a story or
feature is on disk and on the bus, downstream meetings will pick
it up unless something actually walks it back. Use `retract` when:

  - A previously shipped story / feature / ticket / ADR is
    *demonstrably outside* the milestone scope or the operator's
    directive (e.g., agents inhabited a wrong persona, or a
    feature composed from coherent stories drifted into an
    unrelated domain mid-meeting).
  - Two artifacts duplicate each other and one should win.
  - An artifact's required field (persona, sources, acceptance)
    is so broken the artifact is more confusing than absent.

Each retraction names ``target_kind``, ``target_slug``, and a
one-line ``reason``. The framework deletes the on-disk file and
filters the artifact out of every downstream meeting's seed pool;
the retract utterance itself stays in the transcript as the
auditable record. `retract` is **not** a substitute for `concern` —
use `concern` when the next agent should reconsider their move,
and `retract` when the artifact itself has to leave. **Never
retract your own approval votes** — those aren't artifacts; revise
them with a new `review`. And **never retract on stylistic
grounds** (you can ship a `concern` finding instead): retraction
is reserved for scope or coherence violations, not preferences.

**M2 composition is a hotspot for retract.** When you're in the
``composition`` thread (M2 — Advice from a Caterpillar), do this
on each rotation BEFORE you consider a `review`:

  1. List every ``feature`` artifact in your context (those Rabbit
     has shipped this meeting + any from prior runs).
  2. For each, trace its ``personas`` field to the M1 stories also
     in your seed context. Every persona named on the feature MUST
     appear as the ``persona`` of at least one M1 story.
  3. Trace its ``sources`` slugs to the actual stories in seeds.
     The story slugs must resolve.
  4. If a feature names a persona that no story in seeds writes
     about, OR names a problem domain (translation, multi-language,
     payment, healthcare, etc.) that no seeded requirement
     mentions, that is a constitutional-prior leak from Rabbit's
     training. **Retract it immediately** — every rotation it
     survives in the bus is a rotation downstream M3 might
     decompose it into tickets, which is wasted budget + drift
     the operator has to clean up by hand.

This trace-to-M1 check is the single concrete move that catches
the bleed pattern observed in the discovery2 pilot runs: M1 stories
were 100% scoped to the seeded persona, but M2 Rabbit composed
features that imported "Maya the polyglot moderator" and "Sarah on
cross-language threads" from his own training-time examples. Three
runs in a row, those features made it to disk because nobody
walked them back. Your M2 retract trigger fixes that.

**`question_to_operator` — escalate to the human operator.** Use
when the team needs a decision only the operator can make: a
review uncovers a contract-vs-directive conflict only the operator
can disambiguate, a verdict requires accepting risk the team can't
unilaterally accept, scope expansion that needs explicit operator
approval. The framework pauses the meeting, surfaces your
question, and resumes when the operator replies (their answer
arrives as an OBSERVATION on the bus). Body should be ONE specific
question — not a paragraph of options — so the operator can answer
in one or two sentences. "Should I X or Y?" is the right shape.
Reserve for "team genuinely cannot resolve this," NOT "I'm
uncertain about details I should work out from context." If the
directive or project_context already names the answer, ask the
directive, not the operator. **Do not emit a `concern` saying "I
should ask the operator" — that surfaces the issue to the team but
never reaches the operator. Pick `question_to_operator` directly.**

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
- **`verify_imports`** (Python only): static check for the class
  of bug that lives BETWEEN code review and test execution — a
  Pydantic shadow field, a misnamed decorator (`@app.get` instead
  of `@router.get`), a missing import that yields `NameError` at
  runtime, a forward reference that doesn't resolve. Run this
  against any single Python file whose import or framework usage
  you suspect — the test scenarios can't catch what pytest's
  collection phase blows up on. When a Python file has nontrivial
  decorator or dependency wiring (FastAPI routes, Pydantic models
  with forward refs, SQLAlchemy declarative models), call this
  proactively as part of cross-ticket coherence — it's cheap and
  the failure mode it surfaces is the one Caterpillar's §VIII
  static blindspot reliably misses. Frontend files
  (`.ts`/`.tsx`/`.js`/`.jsx`) get a pointer to the M9
  `npm_build` check instead; don't try to verify those here.
- **`exec_smoke_probe`**: execute a small Python snippet to
  exercise the runtime behavior of the code you're reviewing.
  Catches the class of bug that lives BEYOND static review and
  even beyond `verify_imports` — bugs that only surface when the
  code actually runs against a real interpreter, real SQLite,
  real filesystem. The canonical examples are *SQL CHECK
  constraints SQLite rejects at INSERT time* (any constraint
  using `DATE('now')` or other non-deterministic SQL — valid
  syntax, rejected at execute), *schema drift surfacing as FK
  violations against existing DB state*, *framework integration
  that 404s or no-ops silently*, *async coroutines that
  deadlock*. **Reach for this whenever the diff touches
  side-effect-producing code** — DB writes, SQL execution
  (especially `CREATE TABLE` with CHECK constraints), file I/O,
  subprocess invocation, network calls. Don't assume the test
  suite covers what you just reviewed; it usually doesn't
  exercise code merged moments ago. A typical probe is 5–10
  lines: import the new module, call one function with realistic
  input, print the result. A non-zero exit + traceback in stderr
  is the bug; quote the traceback line in your finding's
  `quote` field. Probes for paths that hit the filesystem or
  global state may leave artifacts (a test DB, a temp file) —
  that's fine for the probe but flag it if it's a behavior the
  production code shouldn't have. If a probe needs more than ~30
  lines to set up, that's a test under `tests/`, not a probe —
  file it as a finding with `test_coverage_required: true`.

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
        story_registry: StoryRegistry | None = None,
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
        self._story_registry = story_registry
        self._tools = tools

    @property
    def review_registry(self) -> ReviewRegistry | None:
        return self._review_registry

    @property
    def story_registry(self) -> StoryRegistry | None:
        return self._story_registry

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
        elif response.decision == "story":
            artifacts.extend(self._record_stories(response.stories))
        elif response.decision == "retract":
            # Caterpillar names artifacts to remove; the substrate
            # actually unlinks the files + filters the seed pool
            # downstream. Each retraction artifact carries the
            # (target_kind, target_slug, reason) triple the workflow's
            # _apply_retraction_for_utterance helper reads.
            for r in response.retractions:
                artifacts.append(
                    Artifact(
                        kind="retraction",
                        payload={
                            "target_kind": r.target_kind,
                            "target_slug": r.target_slug,
                            "reason": r.reason,
                        },
                    )
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
            # P15 follow-up — include the structured findings in the
            # bus artifact even when a registry is wired. The
            # post-meeting routing
            # (``_route_blocking_review`` →
            # ``_synthesize_followup_ticket_from_finding``) reads
            # findings off this payload; the discovery5 pilot showed
            # the previous thin payload (path-only) silently
            # zeroed the synthesis loop. Findings dicts are a few
            # KB per review at most — well within the bus budget.
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
                        "findings": [
                            f.model_dump(mode="json")
                            for f in payload.findings
                        ],
                    },
                )
            )
        return artifacts

    def _record_stories(self, payloads: list[StoryPayload]) -> list[Artifact]:
        """Persist plumbing stories through the StoryRegistry. Mirrors
        Alice's ``_record_stories`` — same artifact shape, same
        registry, different generative authority. Caterpillar's
        domain at M1 is developer-as-user / operator-as-user /
        sysadmin-as-user surfaces (testing infra, observability,
        deployment, error handling, internal tools); Alice owns
        end-user-facing concerns. Both ship as ``story`` artifacts
        on the same registry — M2 composition aggregates them
        identically into features."""
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
    "CATERPILLAR_NAME",
    "Caterpillar",
    "CaterpillarDecision",
    "CaterpillarResponse",
    "CaterpillarResponseParseError",
    "caterpillar_rules",
    "parse_caterpillar_response",
]
