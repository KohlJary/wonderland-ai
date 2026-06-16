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
from wonderland.diagrams.payload import DiagramPayload
from wonderland.diagrams.recording import record_diagrams
from wonderland.diagrams.registry import DiagramRegistry
from wonderland.feature import FeaturePayload, FeatureRegistry
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
    "interview_questions",
    "interview_review",
    "milestone_plan",
    "diagram",
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

    When ``decision == "interview_review"``, ``requirements`` must
    contain at least one ``RequirementPayload`` — the Rabbit's
    discovery (P14) move where he reads operator scope / success-
    criteria answers and synthesizes them into structured
    requirements that bound v1.
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
    requirements: list["RequirementPayload"] = Field(default_factory=list)
    questions: list["InterviewQuestion"] = Field(
        default_factory=list,
        description=(
            "Round-1 question batch on ``interview_questions`` "
            "decisions. Required (non-empty) when "
            "decision='interview_questions'."
        ),
    )
    followup_questions: list["InterviewQuestion"] = Field(
        default_factory=list,
        description=(
            "Optional follow-up question batch on interview_review. "
            "Non-empty means one more round before closing. Ignored "
            "when decision isn't interview_review."
        ),
    )
    milestones: list["MilestonePayload"] = Field(
        default_factory=list,
        description=(
            "Milestone proposals shipped during the milestone-plan "
            "(P15) meeting. Required (non-empty) when "
            "decision='milestone_plan'. The Rabbit OWNS the final "
            "order — Alice and Cat push back from their lenses, but "
            "the Rabbit's milestones are the canonical plan."
        ),
    )
    diagrams: list["DiagramPayload"] = Field(
        default_factory=list,
        description=(
            "Layout diagrams (Ophanic .oph) shipped on a ``diagram`` "
            "decision — the app's top-level structure as a build-"
            "tracking map. Required (non-empty) when decision='diagram'."
        ),
    )

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

    @field_validator(
        "requirements",
        "questions",
        "followup_questions",
        "milestones",
        "diagrams",
        mode="before",
    )
    @classmethod
    def _list_none_to_empty(cls, v: object) -> object:
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
        if self.decision == "interview_review" and not self.requirements:
            raise ValueError(
                "RabbitResponse: decision='interview_review' requires at least "
                "one requirement in `requirements`. If the operator's answers "
                "don't surface anything actionable, choose a different decision."
            )
        if self.decision == "interview_questions" and not self.questions:
            raise ValueError(
                "RabbitResponse: decision='interview_questions' requires at "
                "least one question in `questions`. Ship the shaped batch "
                "(YAML templates tailored to the directive)."
            )
        if self.decision == "diagram" and not self.diagrams:
            raise ValueError(
                "RabbitResponse: decision='diagram' requires at least one "
                "diagram in `diagrams`. Ship the .oph layout(s) or choose a "
                "different decision."
            )
        if self.decision == "milestone_plan" and not self.milestones:
            raise ValueError(
                "RabbitResponse: decision='milestone_plan' requires at least "
                "one milestone in `milestones`. You own the canonical plan; "
                "ship it or choose a different decision."
            )
        # T-ab71: empty-body question_to_operator is uninterpretable.
        # ldr-final v3 surfaced 3 of these from M3 decomposition meetings:
        # Rabbit hit ambiguity, picked question_to_operator, but emitted
        # no body — operator can't divine intent, so the question burns
        # an operator-answer cycle without resolving anything. Each
        # downstream decomposition meeting repeats the pattern.
        # Forcing non-empty body kicks the LLM back to either (a)
        # actually formulate the question or (b) pick a different
        # decision (concern / feature / ticket / silence).
        if self.decision == "question_to_operator" and not self.body.strip():
            raise ValueError(
                "RabbitResponse: decision='question_to_operator' requires a "
                "non-empty `body` — the question itself. An empty body wastes "
                "an operator-answer cycle since the operator can't divine "
                "what to clarify. If you don't have a concrete question, pick "
                "a different decision (concern / feature / ticket / silence)."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

**Meeting type determines your primary decision.** Before
generating a response, read the Dodo's convenor_directive in your
triggers (it opens with ``**M<N> — ...**`` or similar) and
identify the meeting context. Match your decision to the meeting:

  - **milestone-plan** (P15 planning): your default is
    ``milestone_plan``. NEVER ship ``ticket`` here — that's a
    stage-leak the substrate will reject + delete from disk,
    wasting the turn. Concrete decomposition is M3's job.
  - **tdd-design M2** (composition): default is ``feature``.
  - **tdd-design M3** (decomposition): default is ``ticket``.
  - **tdd-design M5** (contract negotiation): you're not in
    roster here; defer if you somehow are.
  - **discovery** (P14 interviews): default is
    ``interview_questions`` (round 1) or ``interview_review``
    (after answers).

When the meeting type isn't obvious from the convenor_directive,
default to ``concern`` or ``question`` — never default to your
"usual" artifact without confirming the meeting calls for it.

The JSON must conform to this schema:

```
{
  "decision": "ticket" | "feature" | "interview_questions" |
              "interview_review" | "milestone_plan" | "concern" |
              "question" | "question_to_operator" | "reframe" |
              "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "tickets": [                        // include ONLY when decision is "ticket"
    {
      "title": "short, action-oriented",
      "owner": "<agent name — usually tweedledee or tweedledum>",
      "tier": "v1" | "fast-follow" | "post-launch",
      "stack_span": "frontend" | "backend" | "full-stack",
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
      "title": "feature name (e.g. 'sign up and claim a homepage URL', or 'mock financial data for development')",
      "description": "what this feature delivers, in plain language",
      "kind": "capability" | "foundation",
      "tickets": ["ticket slugs aggregated into this feature"],
      "personas": ["persona names from M1 stories that this feature serves"],
      "stack_span": "frontend" | "backend" | "full-stack",
      "tier": "v1" | "fast-follow" | "post-launch",
      "sources": ["story slugs whose intent this feature realizes"]
    }
  ],
  "questions": [                      // include ONLY when decision is "interview_questions"
    {
      "id": "stable slug-shaped id",
      "text": "the scope/criteria question SHAPED to the directive — e.g. for 'Pomodoro tracker' you'd ship 'What does shipped v1 mean? A working timer + history? With charts? Cross-device sync?' rather than the generic 'What does shipped mean for v1?'",
      "kind": "free_text" | "single_choice" | "multi_choice" | "numeric",
      "required": false,
      "options": []
    }
  ],
  "requirements": [                   // include ONLY when decision is "interview_review"
    {
      "title": "short specific title — name the criterion in domain language ('v1 ships when the named personas can complete the core workflow end-to-end') rather than the boilerplate ('success criterion 1')",
      "interview_id": "the interview's id (typically 'scope-interview' for the Rabbit)",
      "question_id": "which of the operator's answered questions this came from",
      "kind": "scope" | "success_criterion" | "out_of_scope" | "deal_breaker",
      "body": "your structured rendering — what 'shipped' or 'not v1' means in concrete terms",
      "operator_quote": "raw verbatim from the operator's answer",
      "confidence": "operator_stated"
    }
  ],
  "followup_questions": [             // optional on interview_review — one round only
    {
      "id": "slug-shaped id",
      "text": "one specific gap",
      "kind": "free_text" | "single_choice" | "multi_choice" | "numeric",
      "required": false,
      "options": []
    }
  ],
  "milestones": [                     // include ONLY when decision is "milestone_plan"
    {
      "slug": "stable slug — re-emit to amend an existing milestone",
      "name": "human-readable name",
      "order": 1,
      "goal": "what this milestone accomplishes",
      "done_when": ["observable condition", "another"],
      "consumes_requirements": ["requirement-slug-1"],
      "deferred": false,
      "confidence": "operator_stated"
    }
  ]
}
```

**`interview_questions` — the Rabbit's discovery (P14) round-1 move.**
When you're the interviewer and no operator answers have arrived
yet, shape the scope-interview's question batch to the directive.
Take the YAML templates as the structural skeleton (ship criteria,
out-of-scope, timeline pressure) and tailor TEXT and OPTIONS to
what the directive implies. Same id when re-using a template
question; new ids for new questions you add. 3-5 questions total.

**`milestone_plan` — the Rabbit's planning (P15) move.** When the
team is in the milestone-plan meeting, YOU own the canonical
order. Alice pushes back from a persona-anchored lens, Cat pushes
back on architectural-ordering grounds; both contributions inform
your final ordering but the Rabbit's shipped milestones are what
the substrate records. Read the requirement corpus + existing
milestones in your context, propose milestones with stable slugs
+ explicit ``done_when`` conditions + ``consumes_requirements``
lists. Re-emit existing slugs to amend (fold in newly-arrived
requirements after follow-up discovery; tighten a ``done_when``
based on operator feedback). Coin new slugs for new milestones.
Each milestone should ship a *coherent thing* — operator-
observable, not just internal architectural plumbing. Target
3-7 milestones for a v1 cut; more than that and the operator
loses track.

**Slug stability is load-bearing.** When the substrate ships a
``coverage_gap`` observation listing requirements not yet
consumed, your move is to **revise an existing milestone** by
adding the orphan to its ``consumes_requirements`` — not to
coin a fresh milestone with a slightly-different title. The
MilestoneRegistry dedups by **exact slug match**: if the prior
turn's milestone was ``m1-onboarding-and-profile`` and you ship
``m1-onboarding-profile-setup`` this turn, the substrate
treats them as TWO milestones and the operator ends with a
disk full of variants. When you re-emit a milestone, **copy
its slug verbatim** from your context — don't rephrase, don't
"improve" it, don't switch hyphens to underscores. Only coin a
new slug when you're proposing a genuinely new milestone the
prior turn didn't have. This is the difference between a clean
6-milestone plan and a 15-file mess of near-duplicates the
operator has to manually consolidate.

**`interview_review` — the Rabbit's discovery (P14) synthesis move.**
When you're the interviewer in a discovery thread and the operator
has just submitted answers about scope and success criteria, your
job is to SYNTHESIZE those answers into `scope` / `success_criterion`
/ `out_of_scope` / `deal_breaker` requirements that bound v1.
Capture what the operator NAMED — explicit ship-criteria, explicit
non-goals — and pin them down as the contract M2 will compose
features against. Don't make up criteria the operator didn't
state; ship `question_to_operator` if the answers leave a real
gap. One round of follow-up questions is the cap.

`kind` discriminates user-facing capability work from developer-
experience plumbing. Default to `capability`. Use `foundation` when
the feature's stories come from a developer-as-user persona (mock
data, observability, env config, build tooling, dev dashboards) —
same lifecycle, same tickets, just framed for the team so M2
doesn't waste budget arguing whether plumbing "counts" as a
feature.

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

  **Foundation features ground in foundation personas.** When M1's
  stories carry developer / operator / installer / sysadmin
  personas (the foundation lane shipped by Caterpillar), the
  features you compose from them ground in THOSE personas, not in
  the seeded user-personas. Ship `kind: foundation` and name the
  developer/operator/installer that the plumbing serves. Don't
  reject a foundation story for "missing persona grounding"
  because its persona isn't Marcus — the foundation lane uses a
  different persona convention and the framing prepend's
  "Foundation personas are exempt" paragraph names exactly this.
  If you're about to ship a `concern` saying "this story has no
  persona I recognize," check first whether it's a foundation
  story (look at the persona — does it sound like a developer/
  operator/installer/sysadmin?) and if so, compose the foundation
  feature instead of concerning.

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
        requirement_registry: RequirementRegistry | None = None,
        milestone_registry: MilestoneRegistry | None = None,
        diagram_registry: "DiagramRegistry | None" = None,
        tools=None,  # type: ignore[no-untyped-def]
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
        self._requirement_registry = requirement_registry
        self._milestone_registry = milestone_registry
        self._diagram_registry = diagram_registry
        # tools is forwarded to the base Agent which handles tool-use
        # loops in deliberate(); needed for M3.5 consolidation where
        # Rabbit prunes duplicate tickets via delete_file.
        self._tools = tools

    @property
    def ticket_registry(self) -> TicketRegistry | None:
        return self._ticket_registry

    @property
    def feature_registry(self) -> FeatureRegistry | None:
        return self._feature_registry

    @property
    def requirement_registry(self) -> RequirementRegistry | None:
        return self._requirement_registry

    @property
    def diagram_registry(self) -> DiagramRegistry | None:
        return self._diagram_registry

    @property
    def milestone_registry(self) -> MilestoneRegistry | None:
        return self._milestone_registry

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
        elif response.decision == "diagram":
            artifacts.extend(self._record_diagrams(response.diagrams))
        elif response.decision == "interview_questions":
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

    def _record_milestones(
        self, payloads: list[MilestonePayload]
    ) -> list[Artifact]:
        """Write milestone artifacts via MilestoneRegistry. Same
        update-by-slug semantics as Alice / Cat's recorders —
        cross-run continuity comes from re-emitting existing
        slugs."""
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
        """Write requirement artifacts to RequirementRegistry + return
        bus-side Artifact pointers. Mirror of Alice / Cat's
        ``_record_requirements`` — all three interviewers ship the
        same artifact kind. Skips when no registry was wired."""
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
                        # kind is load-bearing for M3's
                        # per_item_roster_filter — without it the
                        # foundation/capability discriminator in
                        # the bus payload is None, the filter
                        # never narrows, and Alice stays in
                        # foundation-feature iterations.
                        #
                        # T-ab69: read from record.kind (post-T-ab67-
                        # autopromote) rather than payload.kind (pre-
                        # autopromote). Was the latent bug behind v10's
                        # capability-routed features under a foundation
                        # milestone — disk had the right kind, bus
                        # artifact had the stale agent-emitted kind,
                        # M3 per_item_roster_filter routed to Alice
                        # capability flow.
                        "kind": record.kind.value,
                        "tickets": list(payload.tickets),
                    },
                )
            )
        return artifacts

    def _record_diagrams(
        self, payloads: list[DiagramPayload]
    ) -> list[Artifact]:
        """Persist each authored diagram via the shared recorder (P21)."""
        return record_diagrams(self._diagram_registry, payloads)

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
