# Workflow walkthrough — how Wonderland actually runs

> Source material for the paper's architecture chapter. Walks every
> meeting in every major workflow: who attends, why each agent is on
> the roster, what the meeting is trying to produce, how the
> substrate enforces the meeting's shape, and what the meeting
> commits when it closes. Written against the YAMLs in
> `src/wonderland/closet/workflows/` as of release 0.8.0.

## Reader's guide

Wonderland's pipeline runs the full software-development lifecycle
in four atomic workflows that an operator composes in order:

1. **discovery** — interview the operator; capture intent as
   `requirement` artifacts on disk.
2. **milestone-plan** — group requirements into an ordered
   trajectory of `milestone` artifacts.
3. **tdd-design** — for a given milestone, produce stories →
   features → tickets → architecture → contracts.
4. **tdd-implement** — for queued features, write failing tests,
   implement against them, review the cohesive deliverable, and
   verify by actually running the project's test suite.

Each workflow is a YAML file that declares meetings (or interviews
in discovery's case), a roster per meeting, a sequence of phases per
meeting, exit conditions per phase, and bookkeeping about how the
substrate transitions lifecycle state. Workflows are intentionally
short — the longest is ~800 lines of YAML, half of that being prose
directives the runtime relays to the agents. The substrate enforces
the rest.

The cast referenced throughout:

- **Alice** — user-voice. Persona-anchored grounding; written to
  recognize when work has drifted from the user the team is
  building for.
- **Caterpillar** — coherence reader. Reviews artifacts against
  what's already on the bus + on disk; checks that claims hold.
- **Cheshire Cat** — architect. Owns ADRs; thinks about structural
  seams and what the system's shape implies.
- **White Rabbit** — planner. Owns sequencing, decomposition,
  composition. Things that ship as ordered lists tend to come from
  Rabbit.
- **Tweedledee + Tweedledum** — implementers. Frontend bias / backend
  bias respectively; pair-protocol negotiation on contracts and
  implementations.
- **Mad Hatter** — adversarial test designer. Edges, failure modes,
  degradations.
- **Queen of Hearts** — security lens. Threat-models features;
  names what we're committing *not* to do.
- **Mock Turtle** — consolidator. Closes milestones by archiving
  per-milestone memory branches and writing project-level summaries.
- **Dormouse + Dodo** — substrate-injected voices. Dodo surfaces
  synthetic observations when coverage checks fail; Dormouse
  appears in narrative continuity roles.

The substrate primitives the workflows lean on:

- **roster** — who can speak at this meeting; everyone else is
  invisible to the bus during that meeting.
- **convenor_directive** — the prose framing the runtime relays to
  the roster at meeting open; layered on top of each agent's
  constitution, scopes "what we're here to do."
- **allowed_decisions** — substrate-level allowlist on artifact
  shapes; emissions outside the list get stripped of artifacts
  before publishing.
- **primary_speaker** — when multiple agents on the roster could
  ship the same artifact kind, the primary's emission survives
  snapshot; the others get filtered.
- **phases** — meetings break into ordered phases (`discussion`,
  `commit`, `review`, …) with their own rotation caps and exit
  conditions. Most meetings are single-phase now.
- **exit_condition_artifact** — phase ends as soon as one agent
  ships an artifact of this kind. No exit_condition → run to
  rotation cap or natural quiescence.
- **per_item** — iteration unit. `per_item: feature` runs the
  meeting once per feature in scope; tickets and milestones do the
  same at their granularity.
- **iterate_only_in_states** — lifecycle gate: skip iteration items
  not in this list of states. Keeps cross-run reruns from
  re-processing settled material.
- **parallel** — when `true` (and the runner supports it), per-item
  iterations run in parallel lanes with thread-isolated bus + memory.
- **per_item_roster_filter** — narrows the roster on a per-item
  basis (`field: kind, map: {capability: [alice, rabbit], foundation: [rabbit]}`).
- **gates_on_dependencies** — within a parallel level, iteration
  items wait for their `Blocked by:` upstream items to finish before
  starting.
- **coverage_check** — substrate runs a check at end of rotation;
  on failure, injects a synthetic Dodo observation and grants a
  bonus rotation (capped). Used at meetings where "everything got
  realized" matters more than rotation budget.
- **seeds** — declarative spec for what utterances + on-disk
  artifacts the meeting can see. `from: <meeting_id>` scopes to a
  prior meeting's bus output; `from: any` includes disk-fallback.
- **transition_iteration_to** — lifecycle state the substrate
  transitions the iteration item to when the meeting closes
  successfully.
- **disallowed_decisions** — workflow-level blocklist; an agent
  who pattern-matches to another workflow's primary decision shape
  can't corrupt the registry.

The cast and substrate primitives are referenced freely below; the
paper's architecture chapter will introduce them more formally.

---

## 1. Discovery — `discovery.yaml`

### Overview

Discovery is the operator's first contact with the system on a
fresh project. Three short focused interviews run in series; each
captures operator answers as `requirement` artifacts on disk under
`.wonderland/requirements/`. There are no meetings — discovery is
interview-only. The operator answers ~12 minutes of questions; the
substrate writes ~15-25 requirement files; downstream workflows
seed from those files instead of re-prompting.

**Budget:** $1.50 (most of the cost is operator attention, not
LLM tokens).

**When to run:** fresh project before any design; existing project
with requirements gaps; existing project whose intent has shifted.
Existing projects with no discovery history should consider
`discovery-backfill`, where agents infer requirements from project
state instead of interviewing the operator.

**Output:**

- `persona` + `situation` requirements (from Alice)
- `constraint` + `integration` + `deal_breaker` requirements (from Cat)
- `scope` + `success_criterion` + `out_of_scope` requirements (from Rabbit)
- Each artifact carries `confidence: operator_stated` — downstream
  meetings trust it without re-confirmation.

### Why three interviewers instead of one

Each character's interview shape matches their lens. Alice asks
about people; Cat asks about constraints; Rabbit asks about scope
boundaries. Mixing those into a single interviewer either drops
quality (one voice trying to cover three frames) or pads the
operator's load (asking everything but treating answers
uniformly). Splitting is cheap — interviews are sequential, ~12
minutes total operator time, and the substrate routes each
question to the right requirement kind based on the interviewer's
identity.

The interviewers don't talk to each other during discovery. There
is no shared deliberation — each interview is operator ↔
interviewer one-on-one, and the requirement artifacts get
composed in the next workflow (milestone-plan) by a different
roster.

### I1 — Persona interview ("Who is this for?")

- **Interviewer:** Alice
- **Estimated time:** 5 minutes
- **Allow followup:** yes (one follow-up round if answers surface
  a gap)
- **Goal:** capture personas + situations that anchor downstream
  design

**Why Alice:** persona work is Alice's identity. Her constitution
trains for specificity in personas — "Maya, 31, polyglot moderator
at a translation startup, end of day, scrolling through 40 pending
threads" beats "the user." Putting any other character here
produces generic personas that drift into stack-talk or
scope-talk.

**Questions:**

1. **primary_persona** (required, free text) — Who's the primary
   person using this? Name + age range + role + what's happening
   in their life when they reach for the project.
2. **situation** (optional, free text) — What just happened to
   them, in the moment when they open this? Surface the trigger.
3. **existing_workflow** (optional, free text) — What do they do
   today instead of using this?
4. **success_signal** (optional, single choice) — task_completed
   / time_saved / anxiety_reduced / delight / other.
5. **deferred_personas** (optional, free text) — Anyone we're
   deferring for v2 / fast-follow?

**Output shape:** Alice synthesizes each answer into one or more
`persona` or `situation` requirements with stable slugs. The
deferred-personas answer becomes one or more `persona`
requirements with `tier: deferred` (so downstream M2 composition
can see them as explicitly-deferred rather than re-introducing them
into v1 scope).

### I2 — Constraints interview ("What can't move?")

- **Interviewer:** Cheshire Cat
- **Estimated time:** 4 minutes
- **Allow followup:** yes
- **Goal:** surface technical constraints, integrations, and
  deal-breakers

**Why Cat:** constraints work is architectural. Cat's constitution
trains for architectural sensitivity — what bounds the solution
space before he proposes anything. Putting Alice here produces
persona-flavored constraints ("Maya needs it fast"); putting
Rabbit here produces scope-flavored constraints ("we need it by
Tuesday"). Cat asks the right question: what about the
architectural space is non-negotiable.

**Questions:**

1. **stack_constraints** (optional, free text) — Any stack choices
   already locked in?
2. **integration_surface** (optional, free text) — What does this
   need to talk to?
3. **scale_target** (optional, single choice) — personal_use /
   small_team / public_beta / production.
4. **deal_breakers** (optional, free text) — Anything that would
   make this a failure regardless of features?

**Output shape:** Cat ships `constraint`, `integration`, and
`deal_breaker` requirements. The deal-breakers requirement kind
is load-bearing — downstream M4 (architecture) reads it to know
what tradeoffs are off the table.

### I3 — Scope interview ("When are we done?")

- **Interviewer:** White Rabbit
- **Estimated time:** 3 minutes
- **Allow followup:** yes
- **Goal:** pin down success criteria + explicit out-of-scope

**Why Rabbit:** scope is a sequencing question and Rabbit owns
sequencing. He asks "when is v1 done" with the planning frame
("what does shipped mean") rather than the persona frame
("would Maya be happy") or the architecture frame ("did we build
the right system"). Out-of-scope is its own load-bearing
artifact kind — naming features the team might propose but you
want to defer prevents M2 from silently composing them in.

**Questions:**

1. **ship_criteria** (required, free text) — What does "shipped"
   mean for v1? Specific enough that three people on the team
   would agree from the same answer.
2. **explicit_out_of_scope** (optional, free text) — Anything
   tempting that's explicitly NOT v1?
3. **access_model** (required, free text) — Who can use the v1
   system, and how do they get in? Single-user local / multi-user
   with accounts / public no login.
4. **timeline_pressure** (optional, free text) — Is there a
   deadline driving this?

**Output shape:** Rabbit ships `scope`, `success_criterion`, and
`out_of_scope` requirements. The access_model answer typically
produces both a `scope` (the chosen access model) and one or more
`out_of_scope` requirements (the access models we're explicitly
not building).

### Discovery's non-decomposable kinds

Three of discovery's seven output kinds — `persona`, `situation`,
`out_of_scope` — and four others (`deal_breaker`, `scope`,
`constraint`, `success_criterion`) are *exempt from
the downstream coverage check*. They don't decompose into features
in the usual sense:

- `persona` + `situation` are grounding context, not deliverables
- `out_of_scope` + `deal_breaker` are negative space — they
  describe what we're NOT building
- `scope`, `constraint`, `success_criterion` apply across the
  whole system rather than mapping to a single feature

Without this exemption, M2 (composition) would chase its tail
trying to compose a feature that "realizes" `persona-marcus` and
the coverage check would never close. The exemption is split into
two sets in `coverage.py`:

```python
_NON_DECOMPOSABLE_REQUIREMENT_KINDS = frozenset(
    {"persona", "situation", "out_of_scope", "deal_breaker"}
)
_NON_REALIZABLE_REQUIREMENT_KINDS = (
    _NON_DECOMPOSABLE_REQUIREMENT_KINDS
    | frozenset({"scope", "constraint", "success_criterion"})
)
```

The orphan check (does every requirement live in *some*
milestone) uses the decomposable set — `scope` + `constraint` +
`success_criterion` DO need a milestone home. The realization
check (does every requirement get realized by some feature) uses
the realizable set — none of the seven kinds need feature
realization.

---

## 2. Milestone-plan — `milestone-plan.yaml`

### Overview

Operator runs this once after discovery. The output is an ordered
sequence of milestone artifacts: foundation ships first, the core
loop second, gamification third, etc. Each milestone names which
requirements it consumes and what observable signal means it's
done.

**Budget:** $1.50 (one meeting, three agents, two phases of
two-rotation cap each).

**Cross-run continuity:** re-running this workflow after a
follow-up discovery AMENDS the existing plan, not replaces it.
Same slug = overwrite; new slug = append. Agents see existing
milestones in their seed pool and revise / extend.

**Target:** 3–7 milestones. More and operators lose track; fewer
and milestones aren't pulling their weight as a sequencing layer.

**Why milestones exist at all:** without them, M2 (composition)
in tdd-design sees all requirements at once and composes features
against a flat pool. Foundation work, user-facing capability, and
deferred follow-on all surface as siblings; the operator can't
sequence implementation. Milestones inject explicit ordering so
each tdd-design run scopes to one milestone (`--milestone <slug>`)
and produces features inside that milestone's frame.

### The single meeting — "The Caucus on the Map"

- **id:** planning / **label:** P1
- **Roster:** White Rabbit, Cheshire Cat, Alice
- **Primary speaker:** White Rabbit
- **Goal:** compose the milestone plan from the requirement corpus
  — ordered, with done-criteria, scoped to consumed requirements
- **Meeting budget:** $1.50
- **Allowed decisions:** `milestone_plan`, `concern`, `deference`,
  `silence`

**Why Rabbit primary:** ordering work is Rabbit's identity. The
substrate-level `primary_speaker: white_rabbit` field has teeth:
any `milestone_plan` emission from non-primary speakers gets
snapshot-cleaned at meeting end. The mvp-demo pilot surfaced the
need — Alice's persona-anchored milestones and Rabbit's
technical-layer milestones both survived in parallel at the same
orders (different slugs at same order), producing 9 milestones
for 5 conceptual positions. Single-author keeps the plan
internally consistent.

**Why Cat is on the roster:** Cat checks architectural ordering.
A proposed sequence that has M4 architecting against a foundation
that hasn't shipped is an architectural smell only Cat reliably
catches — Alice's grounding doesn't surface it (the persona
doesn't care which milestone the foundation ships in) and Rabbit
doesn't always surface it (he's compositionally focused, not
structurally focused). Cat pushes back via `concern`; he does NOT
ship his own `milestone_plan` (primary-speaker enforcement).

**Why Alice is on the roster:** Alice grounds in
persona-shipped value. A proposed order that has the persona
seeing something incomplete-feeling before something
complete-feeling is a persona-recognition smell only Alice
reliably catches — Rabbit's sequencing logic optimizes for
architectural coherence, not "what would Marcus think when this
ships." Alice pushes back via `concern`.

**Why `question` and `question_to_operator` are EXCLUDED from
allowed_decisions:** observed failure mode in the first two runs
— agents asked each other clarifying questions for eleven turns,
shipped zero milestones, and the meeting timed out. The
directive explicitly says "DO NOT ask each other questions";
the allowed_decisions list backs that up at the substrate level.

**Why `milestone_plan` is the only productive output:** discovery
is over by the time this meeting opens. Stories, tickets,
features, ADRs all happen downstream in tdd-design with the
milestone scope as their frame. An agent who pattern-matches to
"design meeting" and ships a `story` or `feature` here is
shipping into the wrong workflow; the substrate strips those
artifacts at snapshot time and the agent burned budget for no
result. The convenor directive enumerates the forbidden shapes
explicitly:

- NO `story` — story composition is tdd-design M1
- NO `interview_questions` — discovery is over
- NO `ticket` — decomposition is tdd-design M3
- NO `feature` — composition is tdd-design M2
- NO `proposal` / ADR — architecture is tdd-design M4
- NO `test_scenario` — testing belongs in tdd-implement

**Coverage discipline:** every requirement must live in at least
one milestone's `consumes_requirements` list. Multi-milestone
membership is expected and good — persona + situation
requirements typically appear in EVERY milestone the persona
would touch; cross-cutting constraints appear in every milestone
they bound. The convenor directive walks through the kind-by-kind
rules.

**Phases:**

| Phase | Max rotations | Exit condition | Coverage check |
|-------|---------------|----------------|----------------|
| `plan` | 3 | none (run to cap or quiescence) | `requirement_coverage` |

**Why no `exit_condition_artifact`:** an early run had Rabbit ship
a milestone_plan on turn 1 and the phase exited immediately because
the exit condition fired — Cat and Alice never got their turn to
refine. The three rotations give each agent ONE turn to ship their
initial position and a second turn to amend or push back. Phase
ends naturally on rotation cap or when everyone passes in
succession (registered quiescence).

**The coverage check (`requirement_coverage`):** after each
rotation, the substrate verifies every decomposable requirement is
consumed by some milestone. If gaps remain, it injects a synthetic
Dodo observation listing the orphan slugs and grants a bonus
rotation so Rabbit can revise. Bonus rotations are capped (default
2). End-of-phase outcome is COMPLETE when coverage closes,
COVERAGE_INCOMPLETE when the cap exhausts — operator notices the
difference in the dashboard.

**Seeds:**

- `project_context` (any) — runtime shape, stack, entry point
- `requirement` (any) — the corpus from disk
- `milestone` (any) — prior plan for cross-run amendment

---

## 3. tdd-design — `tdd-design.yaml`

### Overview

Five meetings (M1 through M5) plus a consolidation pass (M3.5).
Produces designed features — features with constituent tickets,
an architectural commitment, and per-feature contracts — but does
NOT implement them. Operator reviews the designed features, picks
which to queue, runs tdd-implement separately.

**Budget:** $3.00 (sums to ~$2.00 of meeting budgets + per-feature
fanout in M3, M3.5, M5).

**Why the split from tdd-implement:** cost-of-iteration. Design
runs are ~$0.50–$2 territory; implementation is $5–$15. Being
able to iterate design 5–10× before committing implementation
budget is a structural change in the cost curve. Cross-run
continuity (seed-fallback) means refined ADRs and stories from
prior design runs carry forward, so iterating design on the same
project is meaningful work, not redundant regeneration.

**Order rationale (from analysis 040):** stories → features →
tickets → architecture → contracts. Two changes from earlier
shapes:

1. **Features before tickets** (was the other way). Features are
   user-meaningful capabilities; tickets are implementation atoms.
   Stories → features → tickets matches how product → engineering
   decomposes work. The previous order (tickets first, features
   composed from them post-hoc) led to monolithic-feature collapse
   — Rabbit lumped six tickets into one feature because the
   grouping was rationalization, not composition.
2. **Architecture after feature/ticket generation.** Cat
   architecting from concrete features + tickets produces grounded
   ADRs. Cat architecting from stories alone produces abstract,
   less actionable ADRs.

**Hatter is NOT in this workflow.** Adversarial test design (the
red phase of TDD) happens in tdd-implement M6, paired with the
implementation it tests. Designed features ship without test
scenarios; tdd-implement generates failing tests + passing
implementation as a paired loop per ticket.

**Workflow-level disallowed_decisions:**

- `milestone_plan` — a stray emission would overwrite milestones
  with invented slugs (observed failure mode)
- `interview_questions` — discovery's shape, not design's
- `interview_review` — same

**Output:**

- User stories (Alice's M1 work)
- Features grouped by user-meaningful capability
- Tickets per feature
- One or more ADRs
- Zero or more security rulings
- Contract notes per feature
- Features end up in lifecycle state `designed`

### Cross-run filter: `iterate_only_in_states`

Several meetings carry `iterate_only_in_states` filters that scope
their iteration to lifecycle states matching the meeting's job:

- M2 (composition) → composes only when `feature.state == proposed`
- M3 (decomposition) → decomposes only `proposed` features
  (transitions to `in_design` on completion)
- M3.5 (consolidation) → consolidates only `in_design` features
- M5 (contracts) → contracts only `in_design` features
  (transitions to `designed`)

Without these filters, a cross-run design pass would re-process
already-designed features and ship duplicate tickets, duplicate
contract notes, duplicate ADRs. The filter is the cross-run
continuity mechanism — it lets the operator iterate design 5–10×
on the same project without combinatorial regeneration.

### Milestone scoping

When the operator passes `--milestone <slug>` (or the TUI's
"Milestone Design" launcher prefills it), the workflow runner:

1. Loads the milestone's `consumes_requirements` list
2. Narrows the requirement seed pool to that subset
3. Narrows the existing-features seed pool to features whose
   primary milestone matches (strongest-overlap-wins Jaccard
   over story sources)
4. Auto-synthesizes a `convenor_directive` for M1 if the operator
   leaves it blank ("Design milestone <name>: <goal>. M1 already
   shipped <X>; M2 shipped <Y>; leave their territory alone.")

This is what keeps M3 design from re-debating M1 features and
what keeps Alice from drifting into M1-flavored stories during M2
design. The mvp-demo2 pilot was the validation gate for these
fixes — M2 design without auto-synthesized directive wedged on
Alice drift; with it, design recovered.

### M1 — "The Caucus Race" (stories)

- **Roster:** Alice, Caterpillar
- **Goal:** produce user stories from inhabited personas
- **Per-item:** project-wide (single iteration)
- **Meeting budget:** $0.40
- **Convenor directive:** entry meeting — the operator's launching
  directive replaces any convenor directive at runtime.

**Why Alice:** stories are the persona-anchored need statements
that downstream design will compose from. Alice's constitution §V
carries the story shape — persona, situation, need, acceptance
criteria, confusion-flags. No other character ships stories with
this discipline.

**Why Caterpillar on the M1 roster:** two reasons. First, story
shape needs review at the source — does this story have a
confusion-flag, is the persona specific, are acceptance criteria
observable, does it overlap a sibling, is the scope right for v1.
Weak stories propagate silently into M2 composition and produce
weak features; reviewing them at M1 catches the damage early.
Second, bus traffic from two agents helps the meeting actually
quiesce — the prior alice-alone shape sometimes hung in silence
because there was nothing to register quiescence against.

Caterpillar's M1 review is the same review move he plays in
M2/M5/M8, scoped here to story-shape grounding.

**Phases:**

| Phase | Max rotations | Exit condition | Coverage check |
|-------|---------------|----------------|----------------|
| `stories` | 3 | none | `minimum_stories` |

**Why no exit_condition_artifact:** M1 is generative — we want
rotations to run until quiescence (everyone has nothing more to
add) or the cap is hit. Stopping the moment Alice ships her first
story would produce one-story milestones.

**Coverage check (`minimum_stories`):** substrate extends rotation
budget until at least 3 stories ship, capped by
`coverage_max_extra_rotations`. Validation pilots showed M1 can
deadlock even with framing prose; this guarantees rotation budget
extends rather than exiting empty.

**Seeds:**

- `project_context` (any)
- `requirement` (any) — narrowed by milestone if scoped
- `story` (any, `consumed_by: feature`) — only stories without a
  feature sourcing them surface here

The `consumed_by: feature` filter on stories is critical: on
cross-run design passes, stories with existing features get
dropped from M1's seed pool so Alice + Cat don't re-debate
already-composed material. If the directive is already covered,
both agents go silent on the first rotation and the meeting
closes immediately.

### M2 — "Advice from a Caterpillar" (composition)

- **Roster:** Alice, White Rabbit, Caterpillar
- **Goal:** compose user-facing features from the M1 stories
- **Per-item:** project-wide
- **Meeting budget:** $0.40

**Why Rabbit primary author:** composition is sequencing —
grouping stories into the units a stakeholder can describe in
one sentence. Rabbit's identity is composition under structural
constraints.

**Why Alice on the roster:** grounding voice. She wrote the
stories; she catches when a feature has drifted from a story her
persona would recognize, or when a story she wrote has no
feature serving it. Default to silence unless a grounding
intervention is needed.

**Why Caterpillar on the roster:** composition pass. For each
feature Rabbit ships, does the claim hold against the stories
that sourced it? If a feature aggregates incoherent stories or
makes a claim the stories don't support, Cat surfaces the gap so
Rabbit can revise.

**Feature kinds:** features come in two flavors —

- `kind: capability` (default) — user-facing capability from
  Alice's persona-driven stories. Maps to "user can do X."
- `kind: foundation` — developer-experience plumbing from
  Caterpillar's developer-as-user stories: mock data,
  observability, environment config, build tooling, dev
  dashboards. Maps to "the project gains the ability to X." Same
  lifecycle, same tickets, just not a thing a non-developer
  persona would describe.

The split keeps the team from wasting budget arguing whether
plumbing "counts as a feature" — ship it as `kind: foundation`
and move on.

**Dedup discipline:** the convenor directive enumerates a common
composition failure mode — Rabbit ships two features whose
titles + descriptions describe the same user journey with
different framing ("Marcus completes registration to start
onboarding" + "Marcus completes onboarding and is ready to view
his first routine"). The discipline rule: if a candidate
feature's personas overlap with an existing feature's personas
AND its sources overlap, you're shipping a duplicate — pick one
framing and skip the other. Cross-feature ticket consolidation
(T-a5) cleans up some of this damage at end-of-design but the
prevention is at composition.

**Phases:**

| Phase | Max rotations | Exit condition | Coverage check |
|-------|---------------|----------------|----------------|
| `discussion` | 3 | `feature` | none |
| `commit` | 2 | `feature` | `milestone_realization` |

**Why exit_condition on both phases:** without it, discussion
exhausts all 3 rotations before commit can fire, and meeting
budget burns in concern/nudge ping-pong before commit ever ships
a feature artifact (observed in the obol mock-data design pass:
19 calls of concerns, 0 features). With exit_condition on
discussion, the moment Rabbit has enough alignment to ship, he
ships and discussion ends early.

**Coverage check (`milestone_realization`):** at end of each
rotation in commit, the substrate verifies every requirement the
active milestone consumes has at least one feature realizing it
(via the story-level `realizes_requirements` linkage). Triggers
a synthetic Dodo observation listing unrealized requirements and
grants a bonus rotation so Rabbit can compose additional
features. No-op when `--milestone` isn't passed — no scope to
anchor against.

**Transition:** `transition_emitted_to: proposed` — every feature
Rabbit ships enters lifecycle state `proposed`. M3 picks up only
`proposed` features.

### M3 — "The Rabbit's Errand" (decomposition, per feature)

- **Roster:** Alice, White Rabbit (capability features) /
  White Rabbit alone (foundation features)
- **Goal:** decompose each feature into v1 tickets the Tweedles
  can pick up
- **Per-item:** feature
- **Iterate only in states:** `[proposed]`
- **Parallel:** true (feature-level decomposition is structurally
  independent — feature A's tickets and feature B's never
  reference each other's payloads)
- **Meeting budget:** $0.30

**Why parallel:** ticket decomposition for feature A is
independent of feature B. Running them in parallel cuts wall-clock
without bus contention because each lane gets its own thread-
isolated bus + memory namespace.

**Why `per_item_roster_filter` drops Alice from foundation
iterations:**

```yaml
per_item_roster_filter:
  field: kind
  map:
    capability: [alice, white_rabbit]
    foundation: [white_rabbit]
```

Validation3 pilots showed Alice consistently intervening on
foundation features at M3 with persona-grounding concerns, even
though the feature's persona was already settled at M2 and the
framing-prepend exempts foundation personas from the
seeded-whitelist. Her pattern-match instinct at M3 is to question
whether Operator/Developer/Installer count as "real" personas
(answer: yes, for foundation work) — but the question alone makes
Rabbit hesitate and the iteration ships zero tickets.
Substrate-enforced: foundation features decompose with Rabbit
alone; Alice still buzzes in via §III if she sees something
concrete worth raising.

**Why Alice on capability iterations:** same grounding role as M1
and M2 — defend the user-facing point of the tickets. Push back
when a ticket compresses a story past user-recognition or drifts
toward technical convenience.

**Required ticket fields:**

- `title` — what the ticket is, one short phrase
- `owner` — tweedledee (frontend) / tweedledum (backend) / either
- `tier` — v1 / fast-follow / post-launch
- `stack_span` — **REQUIRED**: `frontend` / `backend` /
  `full-stack`. The substrate uses this in M7 to scope
  implementation to just the Tweedle whose side the ticket
  touches. Don't default to `full-stack`; that defeats the
  optimization. `full-stack` only when the ticket genuinely
  requires both sides to ship together as one unit.
- `estimate` — honest read
- `description` — what shipping this ticket means
- `sources` — **REQUIRED**: the parent feature's citation must be
  the FIRST entry. The substrate uses this link to know which
  tickets belong to which feature when tdd-implement iterates
  per-ticket.
- `acceptance` — observable conditions of done

**Aim for 1–4 tickets per feature.** Zero tickets means
undecomposed; 6+ means M2 over-bundled and the feature should
split.

**Phases:**

| Phase | Max rotations | Exit condition |
|-------|---------------|----------------|
| `decompose` | 2 | `ticket` |

**Transition:** `transition_iteration_to: in_design` — each
feature transitions to `in_design` on successful decomposition.

### M3.5 — "A Caterpillar's Edit" (consolidation, per feature)

- **Roster:** White Rabbit, Caterpillar
- **Goal:** consolidate this feature's tickets — merge overlaps,
  prune duplicates, assign explicit blocked-by dependencies
- **Per-item:** feature
- **Iterate only in states:** `[in_design]`
- **Parallel:** true
- **Meeting budget:** $0.30

**Why M3.5 exists:** M3 has two characteristic failure modes —
over-decomposition (one capability sliced into 8 micro-tickets
that should be 3) and missing dependencies (no explicit
`Blocked by:` so M7 implementations race on shared foundations).
M3.5 fixes both per feature, right after M3 while the tickets are
fresh, and before M4's architecture work which would otherwise
be done against an over-decomposed ticket set.

Cuts downstream cost: a feature decomposed into 13 overlapping
tickets in M3 becomes 5–7 right-sized tickets here. M6/M7/M8
iterate over the smaller set, which dominates implementation
spend. Pays for itself ~3–5×.

**Why Rabbit:** he wrote the tickets in M3 and knows which can
merge. Re-emitting a ticket with merged content is the explicit
move.

**Why Caterpillar:** he has the `delete_file` and `retract`
tools. Pruning duplicates is his action — Rabbit re-emits the
merged ticket; Cat retracts (preferred) or deletes (fallback)
the absorbed tickets.

**`delete_file` vs `retract` discipline:** the substrate has a
first-class `retract` decision that names specific
`target_slugs`, removes them from bus + disk, and logs the
action in the transcript. Caterpillar should prefer that.
`delete_file` is the raw escape hatch — reserve it for orphaned
files (a ticket whose markdown exists but never made it to the
bus registry). The validation4 pilot deleted EVERY ticket via
aggressive `delete_file` calls including the freshly-merged
consolidations; `retract` is safer because it's scoped to slugs
Cat can name in writing.

**Hard rule on over-pruning:** never delete more tickets than
you have explicit evidence to retract. A duplicate is two
tickets covering the same acceptance criteria with the same
stack-span. "Adjacent scope" or "could be combined" is NOT
duplication; raise that as a `concern` so the next design pass
addresses it cleanly. If the consolidated count hits zero,
you've over-pruned.

**Assigning `Blocked by:` is the load-bearing job.** M7 reads
these to serialize dependent implementations (`gates_on_dependencies:
true` on M7's meeting). Without them, dependent tickets race
against half-built foundations and produce duplicate divergent
code. Squathero's migration feature surfaced this — 7 tickets in
parallel where most depended on foundation; result was 4
divergent partial implementations of the same module.

**Phases:**

| Phase | Max rotations | Exit condition |
|-------|---------------|----------------|
| `consolidate` | 2 | `ticket` |

### M4 — "A Mock Turtle's Lament" (architecture)

- **Roster:** Alice, Cheshire Cat, Queen of Hearts
- **Goal:** produce architectural commitments (ADRs) and security
  rulings, grounded in the features + tickets the team has shipped
- **Per-item:** project-wide (architecture isn't per-feature)
- **Meeting budget:** $0.40

**Why Cat as ADR author:** structural commitment is architecture's
identity. Cat owns ADRs — storage shape, integration patterns,
data flow — with explicit tradeoffs. Each ADR names what the
alternative would have been and why we're not choosing it.

**Why Queen on the roster:** security ruling pass. Threat-model
each feature: attack surface, what could go wrong, what the team
is committing NOT to do (deferred to fast-follow vs accepted as
inherent risk). One ruling per feature where the threat model is
non-trivial; skip features with no meaningful security posture.

**Why Alice on the roster:** grounding voice — push back when an
architectural decision drifts from the user-facing point of the
features it supports OR drifts from the operator's directive.
Architecture serves the personas + the directive's runtime shape,
not the other way around.

**Why the directive is in the seed pool:** stack constraints
named in the operator's literal launching prompt ("TUI", "CLI",
"mobile app", "web app") are non-negotiable architectural
commitments. If the directive says "TUI" and Cat is considering a
frontend/backend split, the directive seed surfaces the conflict.
Stories paraphrase; the directive is verbatim.

**Phases:**

| Phase | Max rotations | Exit condition | Team grouping |
|-------|---------------|----------------|---------------|
| `discussion` | 2 | `adr` | [[cat, queen, alice]] |
| `commit` | 1 | `adr` | [[cat, queen, alice]] |

**Why exit on first ADR:** squathero produced 11 ADRs at this
meeting for $1.48 (~3.7× budget) — Cat kept shipping ADRs because
nothing exited the meeting. With exit on first ADR, Cat ships
one well-grounded architectural commitment; further architectural
decisions come from operator-driven re-runs of M4 rather than one
mega-meeting that produces 11 overlapping ADRs.

### M5 — "The Pair Protocol" (contracts, per feature)

- **Roster:** Tweedledee, Tweedledum, Alice
- **Goal:** negotiate per-feature contracts informed by the ADR
- **Per-item:** feature
- **Iterate only in states:** `[in_design]`
- **Parallel:** true
- **Meeting budget:** $0.60

**Why both Tweedles:** the seam between frontend and backend is
negotiated, not unilateral. Contract notes name what shape the
team is committing to — function signatures + dataclasses for
in-process, endpoints + envelopes for HTTP. Both sides see the
contract and either confirms or pushes back.

**Why Alice on the roster:** grounding voice — push back when a
contract compresses the user-facing point of a feature past
recognition, OR when a contract drifts from the runtime shape
(HTTP language in a TUI project, etc.). Default to silence;
engage when a seam decision threatens a story Alice's persona
would recognize OR threatens the runtime fact in project_context.

**Runtime-translation directive:** the Tweedles' role names
("tweedledee = frontend bias", "tweedledum = backend bias")
describe a division of labor that interprets DIFFERENTLY in
different runtimes. The convenor directive translates:

- `runtime: tui` — dee = widget/screen/layout; dum =
  data/model/persistence. Boundary is module imports, not HTTP.
- `runtime: cli` — dee = argparse/output formatting; dum =
  subcommand logic + persistence. Same in-process rule.
- `runtime: web` — dee owns browser surface; dum owns API service;
  boundary IS HTTP.
- `runtime: service` — dum carries; dee may not be relevant.

Stack span guides who leads: full-stack → both negotiate together;
frontend → dee leads + dum confirms; backend → dum leads + dee
confirms.

**Contract note shape:**

- `proposed_change` (required, non-empty)
- `current_shape` (existing contract or "n/a, fresh feature")
- `rationale` (why this shape and not the obvious alternative)

**Phases:**

| Phase | Max rotations | Exit condition | Team grouping |
|-------|---------------|----------------|---------------|
| `discussion` | 2 | `contract_note` | [[dee, dum, alice]] |
| `commit` | 1 | `contract_note` | [[dee, dum, alice]] |

**Transition:** `transition_iteration_to: designed` — each feature
transitions `in_design → designed` on successful contract
negotiation. Designed features are eligible for tdd-implement
once the operator queues them.

---

## 4. tdd-implement — `tdd-implement.yaml`

### Overview

Three agent meetings (M6, M7, M8) plus a substrate-only verify
step (M9). Operates on features the operator has explicitly
queued for implementation. Hatter writes failing tests + Tweedles
make them pass per ticket; Caterpillar reviews per feature.
Substrate runs the project's own test suite to catch what static
review misses.

**Budget:** $8.00 (significantly higher than design — actual code
gets written, tests run, multiple iterations per feature).

**Input filter:** only iterates over tickets whose parent feature
is in lifecycle state `queued`. Features in `designed` but not
yet queued get skipped silently — the operator's queue gate is
the explicit signal "implement these now."

**Output:**

- Test files (Hatter's failing tests, then Tweedles' passing tests)
- Implementation code in src/ (or skeleton-equivalent paths)
- Review notes per feature (Caterpillar's verdict + concerns)
- Features end up in lifecycle state `ready_for_review`
- Operator gates `ready_for_review → verified | rejected`

### Pipeline shape — feature-sequential, ticket-parallel

```yaml
pipeline:
  levels:
    - per_item: feature
      parallel: false              # features sequential
      iterate_only_in_states: [queued, in_progress]
    - per_item: ticket
      parallel: true               # tickets within a feature run in pipeline
```

Two-level pipeline:

1. **Outer level (feature):** sequential. One feature at a time.
2. **Inner level (ticket):** parallel pipeline. Within a feature,
   ticket A finishing M6 starts M7 while ticket B is still in M6.

**Why feature-sequential, ticket-parallel:**

- Tickets within a feature are typically more separable (backend
  ticket touches src/api, frontend touches src/ui) so parallel
  ticket execution races on src/ files less than parallel feature
  execution would.
- Feature-sequential keeps the operator's mental model focused —
  watch one feature flow start to finish, then the next.
- The M8 barrier (per-feature review) is a natural sync point —
  Caterpillar reviews the cohesive feature deliverable after all
  tickets converge.

**Cross-lane isolation:** thread ids are namespaced
`pipe.{feature_slug}.{meeting_id}-{ticket_slug}`; seed resolution
drops utterances from other lanes' threads. Lane A's M8
reviewing feature-A's deliverable doesn't see lane B's M6 test
scenarios for feature-B.

**File-level safety:** M7 ships actual src/ code. Tweedles use
diff-based writes (`str_replace`) for surgical edits. With
ticket-parallel within a feature, two tickets touching the same
file is the principal residual risk; per-feature serialization
appears sufficient in pilot data.

### M6 — "A Mad Tea Party" (failing tests, per ticket)

- **Roster:** Mad Hatter, Alice
- **Goal:** produce a failing test grounded in the ticket's
  acceptance criteria — the red phase of TDD's red-green-refactor
- **Per-item:** ticket
- **Iterate only in states:** `[queued, in_progress]`
- **Requires test design:** true (see flag below)
- **Meeting budget:** $0.50

**Why Hatter:** adversarial test design is Hatter's identity.
Surface the edges, failure modes, degradations this ticket has
to handle. Severity-triage every scenario; underclaim if anything.

**Why Alice on the roster instead of the Tweedles:** roster
history is `[hatter, dee, dum] → [hatter, alice]`. The Tweedles'
contribution at M6 was implementation pressure — anti-productive
at red phase — pushed Hatter toward "what's a test we can pass
quickly" rather than "what's a test that captures the acceptance
criterion." Alice's pushback is persona-shaped: "would the
persona recognize this assertion?" That's the right grounding for
test design. Tweedles see the `test_scenario` artifact when they
enter M7 and can buzz in via their selectively-engaging §III
rules if Hatter ships a test that contradicts their M5-negotiated
contract.

**Alice's M6 move differs from M1/M2/M3 grounding:** in tea-party
threads, Alice ships `test_scenario`, NOT `story`. The convenor
directive locks this:

> Your move here is to write *happy-path* test scenarios from your
> persona's POV: "Maya pastes a 200-char draft and expects the
> translated reply within 2s"… If you genuinely have nothing to
> add beyond Hatter's edges, choose `silence` — don't pad the
> thread. Use `decision: "test_scenario"` with the `scenarios`
> array; do NOT use `decision: "story"` in tea-party threads,
> ever.

Without this directive lock, Alice defaults to `story` (her
natural M1 voice) and pollutes the user story pool with
test-shaped duplicates like "As Maya, I want the timeout case to
be handled."

**The `requires_test_design: true` flag:** this is the per-meeting
default. Skip tea-party for tickets whose source/test-design
markers say adversarial scenario design isn't warranted —
review-synthesized tickets (the Caterpillar's
location/quote/concern/request IS the spec), or any ticket
explicitly marked `test_coverage_required: false`. Cost
optimization that shaves ~$0.50/ticket on review-pass follow-ups.
Caterpillar can override per-finding by setting
`test_coverage_required: true` on a finding, which the
synthesized ticket inherits.

**Phases:**

| Phase | Max rotations | Exit condition | Team grouping |
|-------|---------------|----------------|---------------|
| `red` | 2 | `test_scenario` | [[hatter, alice]] |

**Transition:** `transition_iteration_to: in_progress` — each
ticket transitions `queued → in_progress` when M6 closes.

### M7 — "The Tweedle Pair" (implementation, per ticket)

- **Roster:** Tweedledee, Tweedledum
- **Goal:** ship implementation code that makes the failing test
  pass — the green phase of TDD's red-green-refactor
- **Per-item:** ticket
- **Iterate only in states:** `[queued]`
- **Gates on dependencies:** true
- **Meeting budget:** $0.70

**Why Hatter is intentionally NOT on M7's roster:** he keeps
shipping new test scenarios during implementation despite
directive prose telling him to refine, not regenerate. His
sprawling nature is contained to M6 where scenario generation is
the explicit job. If implementation surfaces genuinely new edge
cases, the Tweedles surface a concern and Caterpillar's M8 review
handles it (or it becomes a follow-up ticket back through M6).

**Why both Tweedles default, narrowed by stack_span:**

```yaml
per_item_roster_filter:
  field: stack_span
  map:
    frontend: [tweedledee]
    backend: [tweedledum]
```

Frontend-only tickets only load Tweedledee; backend-only only load
Tweedledum. Full-stack tickets fall through to the full roster.
The non-roster Tweedle can still buzz in via their constitution's
§III selective-engagement when a contract question surfaces —
narrowing only affects who gets priority windows, not who can
emit. Stack-span narrowing cuts M7 cost materially — single-Tweedle
iterations are roughly half the cost of pair iterations.

**`gates_on_dependencies: true`:** ticket whose code depends on
another ticket's implementation waits for that upstream ticket's
M7 to finish before starting its own M7. M6 (Tea Party) still
runs all tickets in parallel because writing a failing test is
independent of the upstream's actual implementation. Dependencies
come from each ticket's `- Blocked by:` markdown line (assigned
by Rabbit + Caterpillar in M3.5).

Squathero's last implementation run pre-gate had 7 migration
tickets all running in parallel where most depended on the
foundational migration setup; result was 4 divergent partial
implementations of the same module. With this gate, the
foundation ticket finishes M7 first, then dependent tickets see
the actual code on disk before writing against it.

**File discipline:** code lives in non-test directories (src/ or
its skeleton equivalent — production code under src/, tests
under tests/, never inline in conftest.py or test_*.py). Tweedles
run the tests after each meaningful change; iterate until green.
Use `str_replace` for incremental edits (cheaper than `write_file`
when only changing part of an existing file).

**Stay scoped to THIS ticket:** if implementation surfaces
cross-ticket coordination needed, surface as a concern; don't
pull adjacent tickets' work into this iteration. The per_item:
ticket scope is calibrated for atomic work.

**Phases:**

| Phase | Max rotations | Exit condition | Team grouping |
|-------|---------------|----------------|---------------|
| `implement` | 2 | `implementation` | [[dee, dum]] |
| `validate` | 1 | `implementation` | [[dee, dum]] |

**No transition fires here.** Feature stays `in_progress` until
M8 reviews; ticket transitions are derived from M8's verdict
routing (`accept` → ticket IN_PROGRESS → DONE; `request-changes`
→ ticket IN_PROGRESS → ABORTED).

### M8 — "The Trial" (review, per feature)

- **Roster:** Caterpillar, Tweedledee, Tweedledum
- **Goal:** review the feature's full deliverable —
  implementation, tests, cross-ticket coherence — produce a verdict
- **Per-item:** feature
- **Iterate only in states:** `[queued]`
- **Meeting budget:** $0.60

**Why Caterpillar primary:** review is coherence reading and
that's Caterpillar's identity. He reads the cohesive deliverable
— not just individual files but the relationships between them.

**Why both Tweedles on the roster:** defend or revise. If
Caterpillar requests changes, the responsible Tweedle either
revises in this meeting (small scope) or surfaces the change as
a follow-up ticket (larger scope). They don't argue against valid
concerns; M8's job is to enforce the team's collective standard
for `ready_for_review`.

**Cross-ticket coherence first (the load-bearing check):** per
analysis 040, the most expensive defects in feature work live
*between* files. A contract note says one thing; the backend
implements 50% of it; the frontend assumes 100% of it. Or a
component gets built but never wired into the app entry point.
Per-file reviews can't catch these — they require reading
multiple files together. The convenor directive enumerates the
order:

1. **Cross-ticket coherence FIRST.** Open these together BEFORE
   any single-file review: the feature's contract note(s), at
   least one backend file the contract names, at least one
   frontend / consumer file the contract names, the app entry
   point. Verify: do all three name the same fields with the same
   semantics? Does the app entry point actually import and render
   the component the work produced, or is it still rendering the
   skeleton's placeholder UI? Contract drift and orphaned
   components are the canonical cross-ticket bugs.
2. **Does the code match the contract?** Per-file walk against
   ADR + contract notes.
3. **Do the tests cover the acceptance criteria?**

If budget runs out partway through, the cross-ticket check (#1) is
the one that has to ship.

**Per-finding `test_coverage_required` flag:** default FALSE and
false is right for almost every finding. Set TRUE only when the
fix introduces a brand-new capability surface that genuinely needs
Hatter's adversarial discipline:

- TRUE: "add JWT validation," "implement conflict resolution UX,"
  "introduce retry-with-backoff," "add multi-tenant request
  scoping"
- FALSE: schema drift, contract mismatch, wrong field name,
  missing null check, tz-aware/naive datetime bug, off-by-one,
  missing error-state handling, typo, missing migration,
  OperationalError-class bugs

Heuristic: if a Tweedle reading the finding could write a test
for the fix in one sitting without needing Hatter's adversarial
discipline, it's false. In a typical review pass, 0–1 findings
out of 5 should carry true.

**Verdict shape:**

- `accept` (ship it, transition tickets DONE; feature rolls up
  to `ready_for_review`)
- `request-changes` (block, name what must change; tickets
  ABORTED + follow-up tickets synthesized)

**Phases:**

| Phase | Max rotations | Exit condition | Team grouping |
|-------|---------------|----------------|---------------|
| `review` | 2 | `review` | [[cat, dee, dum]] |

**Why no separate "defend" phase:** previous shape had a defend
phase running 1 rotation post-exit; on every recent run it tipped
total spend over budget and stranded the lifecycle
`ready_for_review` transition because defend hit MEETING_BUDGET
before COMPLETE could fire. Tweedle defense, if relevant, shows
up as concerns during the review phase before Caterpillar's
verdict lands — the §III selectively-engaging rules let Tweedles
buzz in without a standing roster slot.

**Feature transition is derived, not declared.** No
`transition_iteration_to` on M8. Substrate routes verdicts to
ticket lifecycle; feature state rolls up from the ticket states
(`all-tickets-DONE` → `ready_for_review` without explicit feature
transition).

**Convergence-failure detection (T-a3):** wired into M8's review
path. Each review finding gets fingerprinted by
`(file_location_no_lines, normalized_concern_first_60_chars)`.
If the same fingerprint appears in 3 consecutive review passes,
the substrate detects convergence failure and writes a spec
ambiguity artifact to `.wonderland/spec-ambiguity/`. The class of
bug is "Caterpillar keeps finding the same thing because the spec
is ambiguous"; surfacing the ambiguity to the operator beats
spinning on review rotations.

### M9 — "Verify" (substrate-only check)

- **Kind:** verify (no agents convene)
- **Goal:** run the project's own test suite + frontend build to
  surface structural failures the per-feature review can't catch

**Why M9 exists:** Caterpillar's M8 review reads for coherence,
not import-time correctness. Pydantic shadow fields, unresolved
forwards, malformed decorators — these are class of bug that
reliably misses M8 because Cat reads as a thoughtful human, not
as a Python interpreter. The class yields cheaply to running
`pytest --collect-only` against the project.

**Three-tier verification (ordered cheapest → most expensive):**

1. **pytest_collects** — do the tests import? Catches structural
   bugs (missing imports, Pydantic shadows, malformed decorators)
   for ~30s of cost.
2. **pytest_passes** — do the tests pass? Catches runtime bugs
   M8's static review can't surface — schema drift between
   SQLAlchemy model and live DB, datetime tz mismatches, contract
   drift between test expectations and implementation. Validation5
   feature 2 surfaced three such bugs Caterpillar accepted as
   correct but failed pytest execution; this check closes the gap.
3. **npm_build** — frontend TypeScript + Vite build. Catches the
   orphan-component shape from analysis 040 + any TS errors the
   per-file review missed.

**Skipped paths degrade silently.** Frontend-less skeletons
(python-cli, python-tui, python-fastapi without React) skip
`npm_build` without firing the substrate. Backend-less skeletons
(pure vite SPA) skip pytest paths. Projects with no
pyproject.toml, no pytest, or no tests collected emit
informational events with `outcome=COMPLETE` — they shouldn't
be punished with auto-tickets they can't act on.

**Env-class verify routing (T-a4):** wired into M9's failure
synthesis. When build_check fails with patterns matching
`ModuleNotFoundError`, `npm ERR`, etc., the substrate routes the
finding to an `operator_attention` artifact instead of
synthesizing a Tweedle implementation ticket. The suggestion is
explicit: "run `uv add <pkg>`" or "run `npm install <pkg>`."
Pre-T-a4, M9 failures from missing deps spawned Tweedle tickets
that couldn't solve the problem (Tweedles can edit code, not
package metadata); post-T-a4, the operator gets the right escalation.

**No `transition_iteration_to` line on M8** (and M9 explicitly
fires per feature in the pipelined runner — right after that
feature's M8 — so failures get attributed to the feature whose
tickets just shipped). On failure, M9 synthesizes a system review
on disk and routes through `_route_blocking_review` with
`auto_complete_in_flight_tickets=False`, which queues follow-up
tickets against the same feature. Feature stays out of
`ready_for_review` until those tickets are worked.

---

## 5. The closeout — milestone consolidation (substrate hook)

Not a workflow, but worth documenting because it's the missing
piece of the lifecycle: what happens when a feature transitions
`ready_for_review → verified`.

**Trigger:** operator marks a feature `verified` from the
dashboard. The TUI calls `_maybe_consolidate_milestone_for_feature`,
which checks whether all features in the milestone are now
verified.

**If yes:** the milestone closes. `consolidate_milestone()` in
`src/wonderland/memory/consolidation.py`:

1. Iterates every per-agent `EpisodicStore`.
2. Archives `design:<slug>` and `impl:<slug>` branches — rewrites
   `branch_id` to `archived:<X>` so queries scoped to the active
   branches don't surface stale deliberation.
3. Writes a project-level summary utterance attributed to
   **Mock Turtle** (using `record_at_branch(project_branch=PROJECT_BRANCH)`).

**Why Mock Turtle:** consolidation is Mock Turtle's identity in
the cast. He summarizes the milestone in retrospect, names what
shipped, marks closure. The project-level utterance survives
across subsequent milestones because it's recorded at
`PROJECT_BRANCH` (not at the archived design / impl branches).

**Branching memory (T-a2) is the load-bearing substrate primitive
here.** Per-agent episodic memory is a `ContextVar[str]` scoped
at the task-local level. Each meeting's `_derive_branch_id`
returns the appropriate branch for the workflow + scope:

- `tdd-design`, `tdd-decompose` → `design:<milestone_slug>`
- `tdd-implement` → `impl:<milestone_slug>`
- everything else → `PROJECT_BRANCH`

The contextvar is set at run_workflow entry, with try/finally
cleanup. Query methods accept a `branches=[...]` filter, with
default `inheritance_chain()` returning `[project_branch, own_branch]`.

The mvp-demo pilot wedged for 22+ rotations on a stale
requirement that Alice had argued about in M1's design — her
episodic memory carried the deliberation forward into M2's
scoped design, and she kept re-litigating it. Branching
memory fixed the class: design-branch deliberation doesn't bleed
into impl-branch implementation, and archived design branches
don't bleed into the next milestone's design.

---

## Appendix — substrate primitives that aren't visible in the YAML

Several mechanisms shape how workflows actually run but don't
appear in the YAML declarations. The paper's architecture chapter
will cover these formally; abbreviated here.

### Snapshot semantics

At meeting end, the substrate computes a snapshot of what
artifacts to publish. The snapshot enforces several invariants:

- **Primary speaker filter** — only the primary speaker's
  emissions of a given artifact kind survive (when a meeting
  declares one).
- **Allowed decisions filter** — emissions of disallowed
  artifact kinds get the artifact stripped (the utterance
  survives as transcript).
- **Empty emission guard** — a snapshot with empty `milestones`
  list (or equivalent) no longer wipes the existing registry.
  Pre-fix, an empty milestone_plan emission deleted M1's file
  during the mvp-demo pilot.
- **Workflow-level disallowed decisions** — the
  `disallowed_decisions` block at the top of the workflow YAML
  filters artifacts before they reach any meeting's
  allowed_decisions check.

### Seed-fallback

When a meeting's `seeds` block references a `from: <meeting_id>`
that hasn't run in the current session, the substrate falls back
to reading the corresponding artifacts from disk
(`.wonderland/features/`, `.wonderland/tickets/`,
`.wonderland/adrs/`, etc.). This is what makes cross-run
continuity work — design iterations 5–10× later still see prior
runs' ADRs, contract notes, stories, and features.

Disk-fallback respects the iteration-kind slice (current ticket
or feature scoping) and the parent-feature scoping for sibling
data (M8 reviewing feature-A sees feature-A's contract notes but
not feature-B's). The mvp-demo pilot surfaced multiple cases
where seed-fallback had to be tightened: review artifacts on
retry iterations, contract_note pass-through against
iteration-kind slice, etc.

### Lifecycle registry

Features, tickets, milestones all live in a per-kind registry on
disk under `.wonderland/`. Each registry exposes:

- `list_all()` — full set
- `list_by_state(state)` — lifecycle-filtered subset
- `transition(slug, from_state, to_state)` — explicit transition
  with state-machine validation
- `unlink(slug)` — remove from registry (with audit log on
  MilestoneRegistry per T-a1)

Lifecycle state is the cross-workflow bookkeeping that lets
`iterate_only_in_states` filters work. State transitions fire
from substrate hooks at meeting end (via
`transition_iteration_to` declarations), not from agent
decisions.

### Cross-feature consolidation (T-a5)

Fires at end of `tdd-design/decompose` (M3) before M3.5. Walks
all newly-decomposed tickets across all features and identifies
near-duplicates by source overlap:

- `_parse_ticket_sources()` strips T-g5 `guid:slug` prefix
- `_score_parent_match()` computes Jaccard similarity over
  source slugs
- `find_cross_feature_duplicates()` returns
  `ConsolidationDecision` records
- `consolidate_cross_feature_duplicates()` walks the ticket
  lifecycle PENDING → QUEUED → IN_PROGRESS → ABORTED to retire
  the duplicate

This is auto-fired with no operator action. Pre-T-a5, the
mvp-demo pilot's M2 produced 5 features with 3 M1-overlap
duplicates and the operator had to skip the dupes manually at
queue time. Post-T-a5, most cross-feature duplication closes at
end-of-design.

### Run-id tagging

Every utterance + artifact record gets stamped with the run's
GUID. Timestamp-based attribution breaks under concurrent runs
(two pilots running side-by-side); GUID-based attribution
survives. This is what makes the parallel ticket pipeline in
tdd-implement safe — lane A's utterances are
`pipe.feature-X.implementation-ticket-1` with run-id `01KZ...`,
and lane B's are `pipe.feature-X.implementation-ticket-2` with
the same run-id but different paired suffix. Cross-run data
never collides.

---

## Closing observation — the workflows are short

The longest YAML in this walkthrough (`tdd-design.yaml`) is 813
lines, half of which is prose framing in convenor directives.
The substrate primitives — registries, episodic memory, seed
resolution, snapshot semantics, lifecycle state machines — carry
the load. Workflows declare: who attends, what artifacts they're
allowed to ship, how many rotations before exit, what closes the
phase, what state to transition the iteration item to on
success.

Everything else — the part that would be agent-loop code in
other multi-agent frameworks — is convenor directive prose: the
framing the runtime relays to the agents at meeting open. Prose
because the agents are LLMs and the cheapest tool for shaping
LLM behavior is text. Substrate because behaviors that need to
be guaranteed (you cannot ship a `milestone_plan` if you aren't
primary speaker; you cannot wipe a registry with an empty
emission; you cannot skip the cross-ticket coherence review when
budget is tight — well, you can skip it, but the substrate
records that you did) need to be enforced outside the agent's
deliberative loop.

That split — directive prose for shape, substrate code for
guarantee — is the architectural decision that lets the same
ten characters compose into discovery, milestone-plan,
tdd-design, and tdd-implement without changing constitutions per
workflow. The character is constant; the meeting frames the
move.
