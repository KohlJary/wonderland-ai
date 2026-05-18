# Thesis chapter source

> Source material for the paper's Thesis chapter. Extends the
> canonical [THESIS.md](../../THESIS.md) (5 corollaries, written
> pre-mvp-demo2) with what's been learned through the
> Tier 2 autonomous pilot — most notably a sixth corollary
> (substrate constraint amplifies identity) and updated
> evidence citations across the existing five.
>
> Companion to [evidence-chapter-source.md](./evidence-chapter-source.md);
> the thesis makes architectural claims; the evidence chapter
> validates the predictions those claims make.

## Note on this artifact vs THESIS.md

THESIS.md is the canonical thesis statement that ships with
the repo for casual readers ("what is this project?"). It was
written when the most recent pilot evidence was analyses 027
and 034 (tdd-serial-phased-first-run, NOT mvp-demo2 — the
analyses directory got renumbered after THESIS.md was
written).

This artifact is for paper writers. Longer, more
academic-register, with updated pilot evidence citations and a
new sixth corollary that emerged from substrate work after
THESIS.md was committed. The five original corollaries are
preserved structurally; their evidence sections are updated.

THESIS.md could benefit from being updated to incorporate the
sixth corollary and the mvp-demo2 evidence citations, but that's
a separate editing pass — the canonical statement and the paper
chapter source are allowed to drift slightly without harm.

---

## The architectural claim

**Identity does real work.**

An agent with a constitution it inhabits across many threads
behaves differently from an agent reconstructed from a system
prompt each turn. It accumulates judgment. It develops
calibrated views of its colleagues. It refuses to cross domain
boundaries because the boundary is part of who it is, not a
policy applied from outside.

The contrast that makes this claim non-trivial: in conventional
multi-agent setups, an agent is *role + tools + goals* — a
function defined by what it should do. In Wonderland, an agent
is *character + voice + persistent persona + named failure
modes* — a function defined by who it *is*, which then
constrains what it does. The difference is whether judgment is
**constituted** (Wonderland) or **re-derived from a system
prompt each turn** (conventional).

This is a specific, testable claim. Its falsifier is a
generic-baseline-vs-identity-native eval that produces
matched-on-task comparisons between Wonderland-on-Haiku and a
generic-prompt-on-the-same-model baseline. That harness lives
in roadmap item P7 and is still future work. Until the eval
ships, the [analyses/](../../src/wonderland/closet/analyses/)
directory carries the qualitative observations as the system
gets built out.

What HAS been demonstrated through the iteration history:
six corollaries that follow from the architectural claim,
each with concrete pilot evidence. They are the structure of
the chapter.

---

## Corollary 1 — Identity lets smaller models outperform their expected capabilities

### Claim

Most of the judgment a generic agent has to derive turn-by-turn
— what to engage with, what to refuse, when to stay silent,
who owns this domain — is carried by the constitution itself.
The model isn't being asked to *invent* the discipline on each
prompt; it's being asked to *act in character*, which is a
much easier task.

The default target for Wonderland is Claude Haiku 4.5
(`claude-haiku-4-5-20251001`). This choice is a **thesis
statement, not a cost-savings move**: if identity is doing the
load-bearing work, a small model with a strong constitution
should hold its own against a large model with a generic
prompt.

Framing Haiku as "the budget option" undermines the
experiment. The cost-comparison work is genuinely useful
(it's how we discover whether the thesis holds), but its
purpose is to *test the thesis*, not to *find the cheapest
model that works*.

### Mechanism

Identity carries judgment. A generic agent on each turn has
to re-derive: am I the right speaker for this? what's my
scope here? what would a careful version of this role do?
A constituted agent reads §I-IX of their constitution and the
answers are present.

A Haiku-class model doing the latter has the same effective
capability as a larger model doing the former — the
constitution is doing the work the larger model would
otherwise have to do via raw inference.

### Concrete pilot evidence

- **Early evidence (THESIS.md cites):** analysis 004
  (Showcase 1, /health endpoint) — three of four agents
  correctly chose silence on a concrete operational directive
  because their constitutions named padding, false certainty,
  and orchestration-performance as failure modes to guard
  against. No external policy intervened; the team's silence
  *was* the settlement.

- **New evidence (mvp-demo2):** the Tier 2 autonomous pilot
  completed end-to-end on Haiku 4.5 — 3 milestones designed,
  implemented, and verified for $83.78
  ([analysis 034](../../src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md),
  [cost breakdown](./cost-breakdown-mvp-demo2.md)). An
  independent cold reviewer (a fresh Claude instance, no
  Wonderland context) called the resulting code *"competent,
  above-average code for an MVP"* with *"real engineering
  taste in the search-escaping and timestamp-normalization
  layers"*
  ([code quality artifact](./code-quality-mvp-demo2.md)).
  Haiku produced this output. The constitutions did most of
  the load-bearing judgment work.

- **Schema-as-safety on Haiku:** across 7+ Caterpillar M8
  review passes during mvp-demo, every review finding cited
  real code at real `file:line` locations with verbatim
  quotes. Zero hallucinated findings — non-trivial for a
  Haiku-class model, where fabrication is the standard
  failure mode. The constitution's forced-citation discipline
  did the work the model wouldn't have done on its own
  ([Evidence Pillar 3](./evidence-chapter-source.md#pillar-3--schema-as-safety-forced-citation-prevents-hallucination)).

### Honest scope

- The P7 generic-baseline eval is still future work. Until it
  ships, the strongest claim is "Haiku produces work consistent
  with what identity-bearing-the-work would predict," not
  "Haiku outperforms what generic-prompt-on-Haiku would produce."
- An untested hypothesis exists that Haiku may be
  *architecturally optimal* for Wonderland (operator's
  qualitative observation that Opus might perform worse on
  the substrate). Excluded from evidence chapter; would belong
  in future work as a comparative pilot.

---

## Corollary 2 — Failure modes are part of identity

### Claim

Every constitution in `constitutions/` has a §VIII Failure
Modes section that explicitly names what the character is most
at risk of slipping into. Alice's *"product owner who keeps
adding stories during implementation."* The Cat's *"false
certainty."* The Hatter's *"scenario sprawl,"* *"severity
inflation,"* *"performing chaos."* The Dodo's *"performing
orchestration."* These aren't policies imposed from outside;
they're load-bearing parts of who the character *is*.

This is what makes the project materially different from a
generic multi-agent architecture: **the generic architecture
defines what each agent should *do*; Wonderland defines, with
equal specificity, what each agent should *not do*.** An agent
that recognizes its own characteristic failure mode can
course-correct from inside, rather than waiting for a
guardrail to intervene from outside.

### The Sephirah/Qlipha framing

The shape of this pairing — virtue and its named shadow, both
load-bearing — is older than software. Kabbalistic tradition
pairs each Sephirah on the Tree of Life with its Qlipha: not
a generic evil, but the specific shell that *that* virtue
decays into when ungoverned. The Sephirah Chesed (loving
overflow) has Tzaphiriron (carrion bird) as its Qlipha — the
specific decay that Chesed's particular virtue is most prone
to. Wonderland's §VIIIs follow the same form. Each character's
virtue arrives with its own Qlipha named alongside it, not a
list of generic anti-patterns.

This is structurally important — and worth preserving in the
paper because it's a recognizable intellectual lineage for
readers who'd otherwise frame "failure modes" as a debugging
checklist. The §VIII section isn't engineering boilerplate;
it's a constitutional acknowledgment that every virtue has a
characteristic shadow, and the agent's ability to act from
the virtue depends on naming the shadow.

### Mechanism

§VIII text is part of the prompt prefix the LLM sees on every
turn, not just at constitution-load time. The
failure-mode awareness is constituted — present in the agent's
self-understanding, not bolted on as an external check. An
agent reading "the way I tend to go wrong is X" before each
deliberation has structural access to course-correction that
an externally-policed agent doesn't.

The engagement rules + output protocols encode the guards
structurally where possible (the §III rules become an
`EngagementRules` instance; the §IV "do not issue" list
becomes an `allowed_decisions` filter at the meeting level).
But the §VIII text itself is what the LLM reads when
deliberating, and that's the load-bearing thing.

### Concrete pilot evidence

- **Original (analysis 004):** three agents correctly chose
  silence on the /health directive because their constitutions
  named the failure modes they would otherwise slip into. The
  silence was the settlement; no external policy intervened.

- **mvp-demo2 (multi-lens review producing unrequested
  quality):** the operator observed unsolicited mid-pilot:
  *"we're not just shipping code, it's quality code. They're
  accounting for all types of shit I never would have thought
  to through the review passes."* Each agent's
  §VIII-anchored over-application (Hatter's edge enumeration,
  Queen's adversarial scrutiny, Caterpillar's coherence
  reading) caught what the others missed. The discipline that
  produced exemplary LIKE-wildcard escaping, DOMPurify
  sanitization, and severity-tagged tests citing scenario
  GUIDs was the §VIII pattern at work, observable in the
  shipped artifact
  ([code quality artifact §3](./code-quality-mvp-demo2.md#3-pattern-receipts--whats-genuinely-good)).

### Where this lands in the paper

This is the **load-bearing differentiating claim**. Lead with
it after the architectural claim itself. The Sephirah/Qlipha
framing is the intellectual anchor that distinguishes
Wonderland from "list of anti-patterns for agents." Connect
forward to Evidence Pillar 2 (multi-lens identity-anchored
review) — failure-modes-as-identity is the design choice;
multi-lens review is the operational consequence; quality is
the output.

---

## Corollary 3 — Character-shaped agents degrade visibly, not silently

### Claim

Most LLM pipelines have two outcomes: they succeed, or they
produce silent garbage at the end of a path where data was
missing or contracts were violated. **Character-shaped agents
have a third option: they recognize the failure and recover,
because the recovery is consistent with who they are.**

The recovery isn't a designed feature; it's emergent from
three converging properties:
1. Agents have intentions tied to their constitutions
   (Tweedles want concrete artifacts to negotiate against;
   Caterpillar wants code to read for coherence; Alice wants
   personas she can speak from).
2. The substrate offers multiple data channels (bus + disk +
   memory).
3. The framework gives characters tools to cross between
   channels (`list_files`, `read_file`, `verify_imports`).

When data is missing on the channel a meeting was supposed to
receive it on, a character-shaped agent NOTICES (because the
absence interferes with what they want to do), FLAGS the
discrepancy as a `concern` (because that's the right speech
act for their identity), and REACHES for the alternative
channel (because they have tools). The recovery is graceful
because each agent stays in character — they don't try to
*be* the missing-data-producer; they negotiate against what
exists.

### Mechanism

The literary parallel keeps earning its keep: the recovery
pattern works *because* the agents have characters with
intentions, not despite it. A role-based agent ("the frontend
implementation agent") has no reason to notice the missing
artifact; their job is "produce frontend code for the given
spec." A character-based agent ("Tweedledee, the
frontend-bias half of a pair who fights with his brother
about contracts") has structural reasons to notice — they
want the spec, they have opinions about the spec, the
spec's absence affects what they can do.

### Concrete pilot evidence

- **THESIS.md original:** analysis 027
  (pomodoro-degradation-and-event-leak). Tweedles noticed
  the directive referenced artifacts that didn't exist,
  flagged the mismatch as a `concern`, reached for the
  disk-resident artifacts via their `list_files` /
  `read_file` tools. Stayed within their character roles —
  didn't try to *be the Rabbit*; negotiated against what the
  Rabbit had actually produced.

- **New evidence (Caterpillar's deterministic-on-code
  property):** when the mvp-demo substrate ghost-completed 2
  review-synthesized tickets due to a bug in build_check's
  `_route_blocking_review` sweep, the underlying code bugs
  remained in the codebase. On the next implementation pass,
  Caterpillar's review re-surfaced those findings because
  the code state was the ground truth, not the ticket graph.
  Substrate damage was recoverable through the next review
  pass
  ([Evidence Pillar 4](./evidence-chapter-source.md#pillar-4--convergent-self-repair-with-a-documented-limit)).

- **Newer evidence + limit:** the recovery property has a
  documented limit — it operates on *code state*, not on
  *episodic memory state*. mvp-demo's M4 design wedged on a
  stale requirement even after the substrate fix had shipped,
  because agents' memory of past wedges persisted. The fix
  required an architectural addition (T-a2 branching memory);
  surfacing this limit is part of the corollary's honest
  framing, not a refutation of it.

### Where this lands in the paper

The recovery-pattern story (analysis 027 → Caterpillar's
self-repair → branching memory as the response to the
self-repair's limit) is a tight three-act arc. Use it to make
the case that visible degradation isn't accidental
robustness; it's a property of building characters who notice
when their environment fails them.

---

## Corollary 4 — Production shape as a derived property

### Claim

What a Wonderland team produces is **shaped like what a small
team would produce, including things the directive never
asked for.** This is not a feature you have to remember to
ask for; it falls out of the constitutional grounding.

A generic LLM given a sparse directive ships what was
literally asked — a working single-file MVP. Wonderland on
the same directive ships a different shape: an ADR with named
tradeoffs and open questions, persona-driven user stories
with confusion-flags, test scenarios that distinguish failure
modes from happy paths, a review pass that catches real bugs
by file and line, inline contract references that cite the
ticket they realize.

**Production-shape as a derived property of constitutional
grounding, rather than a feature you have to remember to ask
for.** Vibe-coded MVPs on a sparse directive are throwaway by
default; Wonderland's output is shaped like what a junior
team's couple-day TDD push would produce, with the artifact
trail that lets someone else maintain the result.

### Mechanism

Each character's constitution carries assumptions about what
production-shaped work looks like for their domain. Alice's
personas include the deaf user, the offline user, the
intermittent-network user, because *that's how Alice models
personas* — she over-includes from the persona surface. Cat's
ADRs name tradeoffs because that's what Cat-shaped ADRs are.
Caterpillar's reviews cite line numbers because that's what
his review-shape requires.

The team produces production-shaped output not because
"production shape" was a goal, but because each character's
default work shape IS production shape for their domain.
Hatter writes failing tests in severity-tagged form because
that's how Hatter writes; Queen names threats with citations
because that's how Queen writes. The aggregation produces
shape no individual character is targeting.

### Concrete pilot evidence

- **THESIS.md original:** analyses 034 + 035
  (tdd-serial-phased runs) shipped accessibility coverage that
  the directive never requested. The team produced an
  explicit deaf-user persona (Priya, *"29, deaf software
  engineer"*) and visual + haptic alert scenarios in one run;
  voice-input accessibility in another. Neither was asked for.
  The mechanism is constitutional: Alice grounds in personas,
  and a persona-grounded view of "who actually uses this
  software" includes users with disabilities by default.

- **mvp-demo2 (the same property, code-shaped):**
  - **39 contract/ticket/ruling references scattered across 8
    source files** — inline citations from production code
    back to the design artifacts that justified it. No
    operator asked for this; it's what Caterpillar's M8
    cross-ticket coherence review pulls toward.
  - **Optimistic-locking infrastructure with audit log** —
    revision_id + If-Match header + AuditLog table with
    JSON-encoded state snapshots + state_hash for tamper
    detection. None of this was in the directive ("Build a
    personal markdown notebook web app. Single user, no
    authentication."). It emerged from Queen's M4 ruling
    framing on data integrity + Caterpillar's M3.5
    consolidation discipline.
  - **Severity-tagged tests using Hatter's vocabulary** —
    24 of 61 tests tagged with `breakage` / `silent-wrongness`
    / `degradation` / `curiosity`. The vocabulary lives in
    Hatter's constitution; the tests inherited it because
    Hatter wrote the scenarios they implement.

### Honest scope

- This is **NOT** "Wonderland produces better code than a
  human team." It's "Wonderland produces production-SHAPED
  code by default, where solo agents produce demo-shaped
  code."
- The production-shape property includes things the directive
  doesn't ask for. Sometimes those things are good
  (accessibility, audit trails, contract citations).
  Sometimes those things are unnecessary for the spec'd scope
  (revision_id machinery on a single-user app — built
  correctly, but with bugs that only matter under multi-user
  load the spec doesn't include). The property is shape, not
  scope-judgment.

### Where this lands in the paper

This is the corollary that pairs most directly with the
[code-quality artifact](./code-quality-mvp-demo2.md). Quote
the cold reviewer's verdict (*"competent, above-average code
for an MVP"*) and the specific receipts (LIKE escape
discipline, DOMPurify, severity-tagged tests). The artifact
makes this corollary unusually citable — most thesis-level
claims live in qualitative description; this one has a
verbatim independent review.

---

## Corollary 5 — Friction is the substrate

### Claim

Most multi-agent systems engineer friction *out* —
consensus-seeking loops, reflection passes that smooth
dissent, voting mechanisms that median competing positions
toward agreement. The result reads fluently and ships nothing
real, because nothing in the loop has the standing or the
constitutional grounding to say *no, that's wrong, and here's
the persona-shaped reason why.*

**Wonderland inverts that move: every meeting in the workflow
is engineered friction with a specific shape.** The
implementation that crystallizes out of an M7 phase is shaped
*because* the prior M1 (stories vs scope), M2 (Alice
grounding Rabbit's compression), M3 (Rabbit decomposing into
tickets), M3.5 (Caterpillar pruning duplicates), M4 (Cat ADRs
+ Queen rulings), M5 (Tweedles negotiating contracts), and M6
(Hatter writing failing tests) all ground each other against
each other.

§VIII is the meta-move: each character carries internal
friction between their virtues and their named failure modes,
so the agents aren't only generating friction with each other
— they carry it inside their own constitutions. That's why a
character can recognize when it's about to go off the rails:
the rails are constitutionally specified.

### Mechanism

Generic "AI agents collaborate" stacks have nothing analogous
because they have:
- roles, not characters
- goals, not voices
- consensus, not constitutions

The friction Wonderland engineers isn't conflict for its own
sake. It's the specific friction that produces the specific
output — Alice's persona grounding pulling against Rabbit's
sequencing pressure is what produces persona-anchored
features (not technically-anchored features); Caterpillar's
coherence reading pulling against the Tweedles' shipping
pressure is what produces reviewed code (not just code).

The substrate is the *stage*, the meetings are the
*choreography*, the characters are the *performers*, and
§VIII gives each performer their characteristic stumble. The
performance happens because the choreography forces specific
juxtapositions of character; the audience (the operator) sees
the result of friction, not the friction itself.

### Concrete pilot evidence

The [workflow walkthrough](./workflow-walkthrough.md)
documents this corollary at meeting-by-meeting granularity.
Every meeting's roster + convener directive is engineered
friction:

- **milestone-plan** — Rabbit primary author with Cat + Alice
  as grounding voices. Rabbit's sequencing pressure pulls
  against Cat's architectural ordering concerns and Alice's
  persona-coherence concerns.
- **tdd-design M1** — Alice generating + Caterpillar
  reviewing at the source. Story-shape friction prevents
  weak stories from propagating to M2.
- **tdd-design M5** — Tweedledee + Tweedledum + Alice. The
  pair negotiates the contract; Alice grounds when the
  contract drifts from user-recognition.
- **tdd-implement M8** — Caterpillar + both Tweedles. The
  Tweedles defend or revise; Caterpillar reads for coherence;
  the verdict is the friction-resolved output.

Each meeting could have shipped fewer voices and would have
been cheaper per-meeting. The substrate is opinionated about
which voices belong in each meeting *because* the friction
between them produces the output shape.

### Where this lands in the paper

This is the architectural-philosophy section. Position
against the "consensus and reflection" wisdom in the agent
literature. The §VIII meta-move (friction-as-character) is
what distinguishes Wonderland's engineered friction from
"agents argue more." Both Pillar 2 (multi-lens review) and
Pillar 5 (constraints improve quality) follow from this
architectural commitment.

---

## NEW Corollary 6 — Substrate constraint amplifies identity

### Claim

What's been learned since THESIS.md was written:
**substrate constraints don't impose discipline on agents
from outside; they let identity carry more of the discipline
from inside.** Every substrate primitive shipped to date that
narrowed agent grammar has improved output AND lowered cost.
The substrate compounds with identity rather than competing
with it.

This is the substrate corollary that the original five didn't
have because mvp-demo + mvp-demo2 hadn't run yet when
THESIS.md was written. It's evidence-graded enough now to
promote to thesis-level.

### Mechanism

Per [Evidence Pillar 5](./evidence-chapter-source.md#pillar-5--constraints-improve-quality):
substrate-level constraints constrain the *grammar*, not the
output. Agents still have full freedom WITHIN the structure,
but the structure forces them to confront questions they'd
otherwise paper over.

Connection to Corollary 5 (friction is the substrate):
substrate constraints ARE engineered friction. Where
Corollary 5 names friction-between-characters as the
mechanism for output, Corollary 6 names friction-between-character-and-structure
as a complementary mechanism. The agent has to grapple with
the constraint; the grappling is the work that produces
quality.

Connection to Corollary 1 (small models): substrate
constraints compensate for individual-agent capability
limits. A Haiku-class model with strong constraints does
work that solo would require a larger model. The constraints
are scaffolding that makes capability legible.

### Concrete pilot evidence

Each substrate primitive shipped through the iteration history
is an instance. The full table lives in
[Evidence Pillar 5](./evidence-chapter-source.md#concrete-pilot-evidence-4);
abbreviated here:

- **Snapshot semantics** (P15) → forced agents to think
  "this milestone_plan emission is my FULL view" →
  eliminated duplicate milestone churn.
- **Primary speaker** (P15) → forced single-author lead →
  eliminated parallel-persona / parallel-technical tracks.
- **Active milestone scope blocks** (P19) → forced
  scope-discipline per meeting → eliminated cross-milestone
  scope creep.
- **Branching memory** (T-a2) → forced milestone-bounded
  deliberation → eliminated argument-history bleed (the
  load-bearing Tier 2 autonomy unlock).
- **Schema-as-safety** (forced citation structure) → made
  hallucination structurally harder than honest reading on
  small models.

The surprising consequence: **quality and cost moved together,
not against each other**, every time a substrate primitive
shipped
([Evidence Pillar 1](./evidence-chapter-source.md#pillar-1--quality-cost-coupling)).
This inverts the conventional ML/agent intuition. It's the
clearest evidence that the substrate isn't a tax on the
identity-bearing work — it's the medium in which
identity-bearing work becomes more legible to the system.

### Where this lands in the paper

After Corollary 5 (friction is the substrate). The
relationship: C5 names friction-as-substrate; C6 names how
substrate constraints (which ARE friction in operational form)
compound with character identity rather than competing with
it. Together they make the architectural case for opinionated
substrate over flexible agent prompting.

This is the corollary that pushes back hardest against the
field's conventional wisdom. *"Give LLMs flexibility, write
open-ended prompts, let them figure it out"* is the dominant
advice; Wonderland's evidence runs the opposite direction.
Frame it explicitly as a counter-claim; address the obvious
rebuttal ("isn't this just rigid prompting?") — no, rigid
prompting constrains the OUTPUT; substrate constraints
constrain the GRAMMAR. Agents still have freedom within
structure, but the structure forces them to confront
questions they'd otherwise paper over.

---

## Closing frame

> *Failures are how software gets built.*

The iterative cycle of ship-then-discover-then-fix depends on
recognizing what went wrong. Agents whose failure modes are
part of their identity can participate in that cycle **as
colleagues, not as tools that need supervising out of their
bad habits.**

The thesis isn't "build better agents." It's *"build agents
who can participate in the failure-and-iteration cycle as
colleagues."* The architectural commitments — identity does
real work, failure modes are part of identity, friction is
the substrate, substrate constraints compound with identity —
all serve that one practical end. Wonderland is the
existence proof that you can build software with agents that
way; the paper is the argument for why anyone else might want
to.

### The connection to identity engineering as a discipline

These six corollaries collectively name **identity
engineering** as a research direction:

- Constitute agent character explicitly, including
  characteristic failure modes (Corollary 2).
- Let the constituted identity carry the load-bearing
  judgment a generic agent would have to re-derive
  (Corollary 1).
- Build the substrate to surface character through engineered
  friction (Corollary 5), and let substrate constraints
  amplify identity rather than override it (Corollary 6).
- The resulting system degrades visibly when broken
  (Corollary 3) and produces production-shaped output by
  default (Corollary 4).

Identity engineering is the discipline; Wonderland is one
instance; the paper is the case for the discipline being
worth pursuing beyond this instance.

---

## Notes for the paper writer

A few editorial framings worth preserving from THESIS.md +
extending:

1. **The Sephirah/Qlipha analogy in Corollary 2 is too good
   to drop.** Readers who think "failure modes" = "list of
   anti-patterns" will read past the corollary. The
   Kabbalistic framing makes the depth of the claim legible —
   every virtue has a characteristic shadow; naming the
   shadow is part of constituting the virtue. Keep it.

2. **The literary lineage matters.** The cast is named after
   Carroll's Alice and Wonderland characters (Cheshire Cat,
   Caterpillar, Mad Hatter, Queen of Hearts, etc.) because
   literary characters carry intentions in a way "the X
   agent" doesn't. The recovery pattern in Corollary 3 works
   because the agents *have* characters; the production-shape
   property in Corollary 4 works because the characters carry
   assumptions about what shape work takes for them. Don't
   defang the literary framing as quirky branding — it's the
   point.

3. **The P7 generic-baseline eval is still future work.**
   When the paper discusses Corollary 1, be explicit that
   the strongest empirical claim is "Haiku produces work
   consistent with what identity-bearing-the-work would
   predict," not "Haiku outperforms generic-prompt-on-Haiku."
   Comparative pilot is on the roadmap; acknowledging the
   gap is more credible than overclaiming.

4. **The thesis chapter and the evidence chapter should
   cross-reference, not duplicate.** Each corollary in the
   thesis chapter cites the evidence pillar(s) that validate
   it; each pillar in the evidence chapter cites the
   corollary it follows from. Together they form the load
   path: architectural claim → corollaries (thesis chapter)
   → pillars (evidence chapter) → artifacts (code-quality,
   workflow walkthrough, cast walkthrough, pilot narratives).

5. **THESIS.md itself.** The canonical statement in
   `THESIS.md` predates mvp-demo2 and the sixth corollary.
   Worth a future editing pass to align — but the chapter
   source and the canonical statement are allowed to drift
   slightly without harm. The chapter source is the more
   detailed paper-shaped version; THESIS.md is the
   ship-with-the-repo summary.

---

## See also

- [THESIS.md](../../THESIS.md) — canonical thesis statement
  (pre-mvp-demo2, 5 corollaries).
- [evidence-chapter-source.md](./evidence-chapter-source.md)
  — the five pillars that validate the predictions these
  corollaries make.
- [workflow-walkthrough.md](./workflow-walkthrough.md) — the
  engineered-friction mechanism (Corollary 5) at meeting
  granularity.
- [cast-walkthrough.md](./cast-walkthrough.md) — the
  failure-modes-as-identity pattern (Corollary 2) at character
  granularity.
- [code-quality-mvp-demo2.md](./code-quality-mvp-demo2.md) —
  the production-shape property (Corollary 4) at code
  granularity.
- [analysis 004](../../src/wonderland/closet/analyses/004-first-race.md)
  — silence-as-settlement evidence for Corollaries 1 + 2.
- [analysis 027](../../src/wonderland/closet/analyses/027-pomodoro-degradation-and-event-leak.md)
  — visible-degradation evidence for Corollary 3.
- [analysis 034](../../src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md)
  — mvp-demo2 completion narrative; new pilot evidence
  across all six corollaries.
