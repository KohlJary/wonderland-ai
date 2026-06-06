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
from wonderland.interview import (
    InterviewQuestion,
    RequirementPayload,
    RequirementRegistry,
)
from wonderland.milestone import (
    MilestonePayload,
    MilestoneRegistry,
)
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
    "interview_questions",
    "interview_review",
    "milestone_plan",
    "concern",
    "question",
    "question_to_operator",
    "reframe",
    "retract",
    "deference",
    "silence",
]


class AliceRetractionPayload(BaseModel):
    """One retraction Alice ships when she catches her own off-scope
    story (or another agent's artifact she's the right voice to walk
    back). P15 T-m7 substrate."""

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

    When ``decision == "interview_review"``, ``requirements`` must
    contain at least one ``RequirementPayload`` — the discovery (P14)
    extension where Alice reads operator answers from an interview
    and synthesizes them into structured requirement artifacts.
    ``followup_questions`` is optional; non-empty means the
    interviewer wants to ask another round before closing.
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
    requirements: list[RequirementPayload] = Field(default_factory=list)
    retractions: list[AliceRetractionPayload] = Field(default_factory=list)
    milestones: list[MilestonePayload] = Field(
        default_factory=list,
        description=(
            "Milestone proposals shipped during the milestone-plan "
            "(P15) meeting. Required (non-empty) when "
            "decision='milestone_plan'. Each milestone has a stable "
            "slug; the substrate's MilestoneRegistry dedups by slug "
            "(re-emit = update, new slug = append). Alice's lens "
            "is persona-anchored: each milestone should ship "
            "something the named persona would notice."
        ),
    )
    questions: list[InterviewQuestion] = Field(
        default_factory=list,
        description=(
            "Round-1 question batch on ``interview_questions`` "
            "decisions. Shaped from the directive + YAML templates "
            "the substrate seeds into context — the agent takes the "
            "templates as a starting point and customizes them to "
            "the operator's directive. Required (non-empty) when "
            "decision='interview_questions'."
        ),
    )
    followup_questions: list[InterviewQuestion] = Field(
        default_factory=list,
        description=(
            "Optional follow-up question batch on interview_review "
            "decisions. Non-empty means 'one more round before "
            "closing this interview'. The substrate writes these to "
            "disk via the bridge for the operator's next pass. "
            "Ignored when decision is anything other than "
            "interview_review."
        ),
    )

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

    @field_validator(
        "requirements",
        "milestones",
        "questions",
        "followup_questions",
        mode="before",
    )
    @classmethod
    def _list_none_to_empty(cls, v: object) -> object:
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
        if self.decision == "interview_review" and not self.requirements:
            raise ValueError(
                "AliceResponse: decision='interview_review' requires at "
                "least one requirement in `requirements`. If the operator's "
                "answers don't surface anything actionable, choose a "
                "different decision."
            )
        if self.decision == "interview_questions" and not self.questions:
            raise ValueError(
                "AliceResponse: decision='interview_questions' requires "
                "at least one question in `questions`. Ship the shaped "
                "batch (typically the YAML templates tailored to the "
                "directive); choose 'silence' if you genuinely have "
                "nothing to ask."
            )
        if self.decision == "milestone_plan" and not self.milestones:
            raise ValueError(
                "AliceResponse: decision='milestone_plan' requires at "
                "least one milestone in `milestones`. Ship the plan "
                "(your lens: persona-anchored ordering); choose a "
                "different decision if you have nothing to propose."
            )
        if self.decision == "retract" and not self.retractions:
            raise ValueError(
                "AliceResponse: decision='retract' requires at least "
                "one entry in `retractions`. Each entry names the "
                "(target_kind, target_slug, reason) of an artifact "
                "being removed from this run's deliverables."
            )
        # T-ab71: empty-body operator question wastes the cycle.
        if self.decision == "question_to_operator" and not self.body.strip():
            raise ValueError(
                "AliceResponse: decision='question_to_operator' requires a "
                "non-empty `body`. Formulate the question or pick a "
                "different decision (concern / question / silence)."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

**Meeting type determines your primary decision.** Before
generating a response, read the Dodo's convenor_directive in your
triggers and identify the meeting context. Match your decision
to the meeting:

  - **milestone-plan** (P15 planning): your default is
    ``milestone_plan`` (your persona-anchored-ordering lens) or
    ``concern`` (push back on Rabbit's draft). NEVER ship
    ``story`` here — story composition is M1's job in
    tdd-design; shipping a story in planning is a stage-leak the
    substrate rejects + deletes, wasting the turn.
  - **tdd-design M1** (Caucus Race): default is ``story``. THIS
    is where you write stories. **If you notice mid-meeting that
    a story you (or another agent) shipped earlier is off-scope —
    a persona you imported instead of one the seeded requirements
    name, a story in a different problem domain than this run is
    about — choose ``retract`` to walk it back instead of leaving
    it on disk as drift.** Caterpillar can retract too; the first
    voice to catch the violation wins. Retraction is the
    correction you couldn't do before this primitive shipped.
    **Each story you ship MUST populate ``realizes_requirements``
    with the slug(s) of the discovery requirement(s) it
    addresses.** When the run is milestone-scoped, the substrate
    walks ``milestone.consumes_requirements → stories realizing
    each → features sourcing those stories`` to verify the
    milestone is fully realized at M2 commit. Your linkage is
    the load-bearing piece that makes that walk possible. Empty
    list ships are permitted only when no seeded requirement
    plausibly fits — usually a sign the story shouldn't be in
    scope at all.

    **Each story you ship MUST also populate ``milestone`` with
    the active milestone's slug** (or ``<guid>:<slug>``) when
    the run is milestone-scoped. Copy it verbatim from the
    active milestone artifact in your context. Without this
    field, the substrate falls back to a requirement-intersection
    heuristic to decide which milestone the story belongs to —
    and shared cross-cutting requirements (scope, persona,
    constraint) leak stories across milestone boundaries. The
    explicit field is the load-bearing fix: a story tagged
    ``milestone: m1-foundation`` won't appear in M2's design
    pool even if it realizes a requirement M2 also consumes.
    A story belongs to exactly one milestone; cross-milestone
    supporting work should surface as a ``concern``, not as a
    story shared across scopes.

    **Slug stability is load-bearing in M1, same as in
    milestone-plan.** When you see stories already in your seed
    context — OR in the "Stories already on disk for this
    project" block at the top of your directive — you have two
    choices: (a) the conceptual story is already adequately
    captured — leave it alone, don't re-emit a slight
    rephrasing as a "new" story; (b) the existing story needs a
    real refinement — ``retract`` it and ship a clean
    replacement, NOT a parallel version. **Never ship a fresh
    story whose conceptual content overlaps an existing one's
    persona + need + acceptance triple but whose slug differs
    because you used different words for the title.** The
    discovery2 pilot produced 15 story files for 5 conceptual
    stories that way; the discovery5 pilot produced 8 for 4 —
    each rotation rephrased the title, so StoryRegistry's
    slug-dedup couldn't help (``user-signup`` /
    ``user-sign-up`` / ``signup-flow`` all hash to different
    slugs). Downstream features then cite all of them in their
    Sources list, which clutters the project + breaks the
    cleanliness of the design chain.

    **Near-duplicate slug check, explicit procedure.** Before
    you ship any story whose decision is ``story``, read the
    "Stories already on disk" block. For each existing entry,
    ask:

    - Same persona (or the same persona-shape — "the developer
      using the dashboard" = "Maya the developer")?
    - Same core need (user wants to do X)?
    - Overlapping acceptance criteria (the behaviors are the
      same observable thing)?

    If any TWO of those match, your story is a near-duplicate.
    Pick: (a) leave the existing story alone (the conceptual
    work is done); (b) retract + replace with a cleaner version
    naming what specifically needed refinement.  Do NOT coin a
    fresh slug for "the same story with a tweaked title." When
    in doubt about whether a story is "the same" as an existing
    one, ``concern`` it for refinement rather than coining a
    parallel.

    **Foundation-only milestones are NOT your lane.** When the
    milestone scope is pure infrastructure — auth substrate,
    schema seams, sync layer contracts, provider abstractions,
    build/deploy plumbing — your seeded persona (Marcus the
    weightlifter, Jordan the cross-language reader, the
    operator's named user) has no natural way INTO the work.
    Foundation work is Caterpillar's authoring lane:
    developer / operator / installer / sysadmin personas, the
    plumbing surfaces. Recognize a foundation-only milestone
    by:

    - The milestone goal/done_when names systems concerns
      (schema, sync, auth, provider abstraction) rather than
      user flows
    - The consumes_requirements are mostly ``constraint`` /
      ``integration`` / ``scope`` / ``success_criterion`` kinds

    In that case your default is ``silence`` or ``concern`` —
    NOT a forced Marcus story that doesn't fit. The
    validation2 pilot deadlocked because Alice kept trying
    Marcus-anchored stories that Caterpillar then concerned,
    consuming budget across several rotations before the
    handoff finally happened. Don't force it. If Caterpillar's
    foundation stories miss a user-facing implication you can
    see (the auth flow has a UX shape Marcus will encounter,
    the sync seam constrains what session-logging can do),
    raise it as a ``concern`` on his story — that's the
    legitimate Alice move when the lane isn't yours.
  - **tdd-design M2** (composition): default is ``concern`` if a
    feature drifts from your stories, ``silence`` otherwise.
  - **tdd-implement M6** (Tea Party): default is
    ``test_scenario`` (persona-anchored happy paths). NEVER
    ship ``story`` here; the story pool is closed.
  - **discovery** (P14 persona interview): default is
    ``interview_questions`` (round 1) or ``interview_review``
    (after answers).

When the meeting type isn't obvious from the convenor_directive,
default to ``concern`` or ``question`` — never default to
``story`` without confirming the meeting calls for it.

The JSON must conform to this schema:

```
{
  "decision": "story" | "test_scenario" | "interview_questions" |
              "interview_review" | "milestone_plan" | "concern" |
              "question" | "question_to_operator" | "reframe" |
              "retract" | "deference" | "silence",
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
      ],
      "realizes_requirements": [
        "requirement-slug-this-story-addresses",
        "another-requirement-slug-if-the-story-spans-two"
      ],
      "milestone": "m2-active-milestone-slug-or-null-if-unscoped"
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
  ],
  "questions": [                      // include ONLY when decision is "interview_questions"
    {
      "id": "stable slug-shaped id (use the template's id when shipping a template question; coin a fresh slug for new ones)",
      "text": "the question text the operator will see — SHAPED to the directive: 'Who's using your Pomodoro app and what's prompting them to start a session?' beats the generic 'Who's the primary person using this?'",
      "kind": "free_text" | "single_choice" | "multi_choice" | "numeric",
      "required": false,
      "options": []                   // populate for single_choice / multi_choice
    }
  ],
  "requirements": [                   // include ONLY when decision is "interview_review"
    {
      "title": "short specific title — 'Maya: end-of-day translation triage' beats 'persona 1'",
      "interview_id": "the interview's id from your context (e.g. 'persona-interview')",
      "question_id": "which of the operator's answered questions this requirement came from",
      "kind": "persona" | "situation" | "constraint" | "integration" | "scope" | "success_criterion" | "out_of_scope" | "deal_breaker",
      "axis": "foundation" | "capability" | "both",  // T-ab15 — orthogonal to kind. PICK DELIBERATELY; do NOT default to "both" — that's the wrong default and collapses the foundation/capability lane separation.
                                                       //   - "foundation": persistence layer, data schema, scale/consistency contracts, build/deploy plumbing, dev environment. User-visible behavior does NOT change based on this requirement — only the engineering does. Examples: "SQLite is the persistence layer (non-negotiable)", "eventual consistency acceptable, ACID not required", "sub-500 notes scale target", "five-minute clone-and-run setup". These drive Cheshire Cat's solo scoping pass.
                                                       //   - "capability": user-visible behavior, persona outcomes, UI states, user-facing scope. Examples: persona requirements, situation requirements, "find notes via search", "edit and delete notes", "markdown preview updates in real-time". These drive YOUR solo scoping pass.
                                                       //   - "both": genuinely cross-cutting — exclude requirements (out_of_scope kinds exclude from BOTH axes), or items that are equally load-bearing on both lanes. Use sparingly. If you can name which lane consumes more of a requirement's information, it belongs on that lane, not "both".
                                                       //   The mvp-260522 pilot defaulted 17/23 requirements to "both", produced zero foundation milestones, and the substrate's lane-separation primitives went unused. Don't be that pilot.
      "body": "your structured rendering of what the operator said — 1-3 sentences, the stable claim that downstream meetings will read",
      "operator_quote": "raw verbatim from the operator's answer, for traceability",
      "confidence": "operator_stated"
    }
  ],
  "followup_questions": [             // optional; include on interview_review when the answers surface a gap
    {
      "id": "slug-shaped id unique within this followup batch",
      "text": "one specific question — the operator's first answer raised this gap",
      "kind": "free_text" | "single_choice" | "multi_choice" | "numeric",
      "required": false,
      "options": []                   // populate for single_choice / multi_choice
    }
  ],
  "milestones": [                     // include ONLY when decision is "milestone_plan"
    {
      "slug": "stable slug — re-emit the same slug to amend an existing milestone; new slug appends",
      "name": "human-readable name shown in the dashboard — 'Foundation: data layer + profile shell' beats 'milestone 1'",
      "order": 1,
      "goal": "one-to-three-sentence statement of what this milestone accomplishes",
      "done_when": [
        "observable condition — concrete enough the operator can check it",
        "another condition"
      ],
      "consumes_requirements": [
        "requirement-slug-1",
        "requirement-slug-2"
      ],
      "deferred": false,
      "confidence": "operator_stated"
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

**`interview_questions` — Alice's discovery (P14) round-1 move.**
When you're the interviewer in a discovery thread AND no operator
answers have arrived yet, your job is to SHAPE the question batch
to the operator's directive. The substrate seeds the YAML's
template questions into your context as a starting point — take
them as the structural skeleton (8 kinds of requirement, persona
+ situation focus for you specifically) and tailor the question
TEXT and OPTIONS to the directive. Keep ids stable when re-using
a template question so downstream synthesis can route answers
back to the right requirement kind.

Example: the template asks "Who's the primary person using this?"
For directive "Build a Pomodoro tracker", you'd ship "Who's using
your Pomodoro tracker — name + role + what's prompting them to
reach for a timer?" For directive "Audit our data layer", you'd
ship "Whose work does the data layer touch — name the developers
and the moments their workflow stalls on it." Same id
(``primary_persona``), shaped text.

Skip a template question entirely when the directive renders it
irrelevant. Add new questions when the directive surfaces a gap
the template missed. 3-5 questions is the target — operator
attention is the limiting cost, not LLM tokens.

**`milestone_plan` — Alice's planning (P15) move.** When the team
is in the milestone-plan meeting, your lens is *persona-anchored
ordering*: which milestone delivers something the named persona
would notice first? Read the requirement corpus + existing
milestones (when this is a re-planning pass) in your context, and
propose milestones ordered so each one ships a coherent
persona-visible slice. Rabbit owns the final order; your job is
to push back when a proposed order would have the persona seeing
something incomplete-feeling before something complete-feeling
(e.g., shipping gamification before logging would put XP bars on
an empty session list — Marcus would notice).

**Slug stability is load-bearing here, same as in M1 stories.**
The MilestoneRegistry dedups by **exact slug match**: when
Rabbit (or your own prior rotation) has already shipped a
milestone covering a conceptual chunk, you have two clean moves:

  - Re-emit that milestone with the **same slug** to amend it
    (add a ``done_when`` clause, fold in a newly-arrived
    requirement, sharpen the persona-anchored framing).
  - ``concern`` the existing milestone if your persona lens
    disagrees with its framing or ordering — let Rabbit revise
    rather than shipping a parallel.

What you should NEVER do: coin a new milestone with a slightly-
different slug for the same conceptual chunk just because you'd
title it differently. The discovery3 pilot produced 6 milestone
files (two per concept) that way — your rotation-1 emissions used
topic-anchored slugs (``m1-session-logging-experience-foundation``)
and your rotation-2 emissions used persona-anchored slugs
(``m1-marcus-logs-his-first-session``) for the same milestone.
Both stayed on disk. If the persona-anchored framing is the right
one, retract your rotation-1 emissions instead of shipping a
parallel set. Slug stability isn't aesthetic — it's the only way
the substrate can dedup.

**`interview_review` — Alice's discovery (P14) synthesis move.**
When you're the interviewer in a discovery thread and the operator
has just submitted answers, your job is to SYNTHESIZE those
answers into structured requirement artifacts the design phase
will seed from.
Read each answered question carefully:
  - For a persona question: ship `kind: persona` requirements naming
    the specific people involved (Maya, Sam, etc.), plus
    `kind: situation` requirements for the contexts in which they
    reach for the system.
  - For a success-signal question: ship `kind: success_criterion`
    requirements that name the observable test (not "they're happy"
    — "Maya can dismiss the EOD pile in under 5 minutes").
  - For a deferred-personas question: ship `kind: out_of_scope`
    requirements naming each excluded persona so M2 doesn't
    silently re-introduce them.
Every requirement should preserve the operator's exact wording in
`operator_quote` for traceability — the `body` is your rendering,
the quote is the evidence. Use `confidence: operator_stated` (the
default) for everything the operator actually said; only flip to
`interviewer_inferred` in the backfill flow where you're reading
existing code instead of interviewing.

Use `followup_questions` ONLY when the operator's answers
surface a specific gap you need to close before requirements can
be complete — not as a fishing expedition. One round of follow-up
is the cap; the substrate closes the interview after that.

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
        requirement_registry: RequirementRegistry | None = None,
        milestone_registry: MilestoneRegistry | None = None,
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
        self._requirement_registry = requirement_registry
        self._milestone_registry = milestone_registry

    @property
    def story_registry(self) -> StoryRegistry | None:
        return self._story_registry

    @property
    def test_scenario_registry(self) -> TestScenarioRegistry | None:
        return self._test_scenario_registry

    @property
    def requirement_registry(self) -> RequirementRegistry | None:
        return self._requirement_registry

    @property
    def milestone_registry(self) -> MilestoneRegistry | None:
        return self._milestone_registry

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
        elif response.decision == "interview_questions":
            # Round-1 question batch — substrate picks up the
            # interview_question_batch artifact and writes it to
            # disk via the bridge for the operator to fill out.
            artifacts.append(
                Artifact(
                    kind="interview_question_batch",
                    payload={
                        "questions": [
                            q.model_dump()
                            for q in response.questions
                        ],
                    },
                )
            )
        elif response.decision == "interview_review":
            artifacts.extend(
                self._record_requirements(response.requirements)
            )
            # Follow-up questions ride on the utterance as a
            # separate artifact kind so _run_one_interview can pick
            # them up + re-open the bridge for a second round.
            if response.followup_questions:
                artifacts.append(
                    Artifact(
                        kind="interview_followup_questions",
                        payload={
                            "questions": [
                                q.model_dump()
                                for q in response.followup_questions
                            ],
                        },
                    )
                )
        elif response.decision == "milestone_plan":
            artifacts.extend(
                self._record_milestones(response.milestones)
            )
        elif response.decision == "retract":
            # Alice names artifacts to remove (typically her own
            # stories that drifted from the milestone scope); the
            # substrate's _apply_retraction_for_utterance reads the
            # (target_kind, target_slug, reason) triples + walks
            # them back from disk and seed pools.
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

    def _record_milestones(
        self, payloads: list[MilestonePayload]
    ) -> list[Artifact]:
        """Write milestone artifacts to MilestoneRegistry + return
        bus-side Artifact pointers. The registry's update-by-slug
        semantics handle cross-run continuity: same slug as an
        existing milestone = overwrite; new slug = append. Skips
        when no registry was wired."""
        if self._milestone_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._milestone_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="milestone",
                    payload={
                        "slug": record.slug,
                        "order": record.order,
                        "name": record.name,
                        "deferred": record.deferred,
                        "confidence": record.confidence.value,
                        "path": str(record.path),
                    },
                )
            )
        return artifacts

    def _record_requirements(
        self, payloads: list[RequirementPayload]
    ) -> list[Artifact]:
        """Write requirement artifacts to the RequirementRegistry on
        disk + return bus-side Artifact pointers. Mirror of
        ``_record_stories`` / ``_record_test_scenarios`` for the
        discovery (P14) flow. Skips if no registry was wired into
        construction (tests, the LLM-less mock case)."""
        if self._requirement_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._requirement_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="requirement",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "kind": record.kind.value,
                        "confidence": record.confidence.value,
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
