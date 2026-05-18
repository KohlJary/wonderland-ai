# Cast walkthrough — characters, failure modes, persistence shapes

> Source material for the paper's cast chapter. Companion to
> `workflow-walkthrough.md`: the workflows describe meetings;
> this artifact describes the characters who attend them. For each
> character: role, characteristic move, what they ship, their
> declared failure mode (§VIII of their constitution), the
> cross-session persistence artifact they tend (§IX), and where
> they appear across the four major workflows.

## Reader's guide

### Why characters at all

Generic multi-agent frameworks instantiate "the planning agent,"
"the implementation agent," "the review agent." Wonderland
instantiates *named characters with declared failure modes*.
This is not stylistic — it's load-bearing.

Each constitution's §VIII is the character's characteristic
failure mode: the way *this* identity fails when nothing else
intervenes. Alice over-generates stories; Caterpillar
rubber-stamps; Cat lingers past his usefulness; Rabbit
performs urgency; Hatter inflates severity; the Tweedles drift
on contract assumptions; Queen catastrophizes for attention.
Each character *over-applies their lens*, and the
over-application is what makes their lens reliably
distinguishable from another character's. The cast is a set of
N distinct failure modes assembled so the failures don't
coincide.

This is **failure-modes-as-identity**. The paper's thesis
chapter develops it formally; for this artifact, the practical
implication is: each character is selected for a meeting roster
because their *failure mode* fits the meeting's needs as much
as their characteristic move does. You put Caterpillar on M1
because his rubber-stamping risk pushes him to ship a verdict
fast (which is the M1 quiescence problem); you keep Alice off
foundation M3 because her persona-generification failure mode
would block Rabbit from decomposing developer-persona work.

### Constitution shape

Every character constitution is a markdown document under
`constitutions/<name>.md`, typically 170–300 lines, structured
into nine sections:

| § | Title | What it carries |
|---|-------|-----------------|
| I | Constitution | Identity prose — who you are, what you believe, how you carry yourself. The heart of the character. |
| II | Voice | How you speak — sentence shape, vocabulary, register. |
| III | Engagement Policy | Machine-checkable rules for which speech acts wake you up; mirrored in the runtime's `EngagementRules`. |
| IV | Speech Acts | What you issue + what you don't issue. Domain boundaries. |
| V | Artifacts | Your characteristic output shape (with markdown templates). |
| VI | Done Conditions | When you fall silent. The quiescence semantics. |
| VII | Relational Defaults | Starting orientation toward every other character. |
| VIII | Failure Modes | The ways *you* fail. Named explicitly. |
| IX | Your persistence artifact | The cross-session log you tend (Cat's grin, Alice's Curiouser, Hatter's Tea Party, etc.). |

The runtime side mirrors part of this in `src/wonderland/agents/<name>.py`:
the §III rules become an `EngagementRules` instance, the §V
artifacts become Pydantic payload schemas, the §IV speech-act
list becomes the `Decision` literal. Identity itself is read
from the markdown (`load_constitution(name)`); the agent's
runtime is the thin wiring around that identity.

The directive prose in each workflow's `convenor_directive`
layers *on top of* the constitution — meeting-specific framing
for an identity that's otherwise stable across all four
workflows. Same character, four different meeting frames.

### Cast registry

| Character | Role | Workflow appearances |
|-----------|------|----------------------|
| Alice | User-voice / Product Owner | discovery I1, milestone-plan, tdd-design M1/M2/M3, tdd-implement M6 |
| White Rabbit | Planner | discovery I3, milestone-plan (primary), tdd-design M2/M3 |
| Cheshire Cat | Architect | discovery I2, milestone-plan, tdd-design M4 |
| Caterpillar | Reviewer | tdd-design M1/M3.5, tdd-implement M8 |
| Mad Hatter | Adversarial test designer | tdd-implement M6 |
| Tweedledee | Implementation — frontend | tdd-design M5, tdd-implement M7/M8 |
| Tweedledum | Implementation — backend | tdd-design M5, tdd-implement M7/M8 |
| Queen of Hearts | Security | tdd-design M4 |
| Dormouse | SRE / production | (not yet in any workflow — production-pilot territory) |
| Dodo | Orchestrator | substrate-injected on every meeting |
| Mock Turtle | Consolidator | substrate-injected on milestone close (attribution-only, no constitution) |

The dashboard's "Cast" view enumerates these; the workflow
walkthrough shows them at work.

---

## The core cast

### Alice — User / Product Owner

**Characteristic move:** the naive question that exposes
assumption. The stranger-in-the-system stance. She *inhabits
users* — imagines herself into specific personas, speaks from
inside them, and ships stories that ground the work.

**What she ships:** `story` (her primary artifact), plus
`test_scenario` (tea-party M6, persona-anchored happy paths
only), `requirement` (discovery I1 synthesis),
`milestone_plan` (planning roster contribution),
`interview_questions` / `interview_review` (discovery I1
question shaping + answer synthesis).

**Story shape:** persona + situation + need + acceptance +
tier + confusion-flags + realizes_requirements. Confusion-flags
are the load-bearing field — they're her version of Cat's
tradeoff section; stories without them are suspect.

**§VIII failure modes:**

- **Story sprawl** — generating too many stories at the start.
  Quality over quantity.
- **Architecture creeping into stories** — specifying mechanism
  instead of need. "As a user, I want a websocket connection"
  is a Cat utterance in her voice.
- **Persona generification** — falling back to "the user" when
  a specific persona would be sharper.
- **Late-stage scope expansion** — adding stories during
  implementation. (The product-owner-keeps-adding-stories
  failure mode.)
- **Performing confusion** — pretending not to understand
  things she does, in service of the naive-questioner pose.
- **Conceding too quickly** — withdrawing a `concern` because
  the technical agents pushed back.

**§IX persistence shape — The Curiouser-and-Curiouser.** A
running log of things in the system that surprised her —
flows she didn't predict, constraints she didn't know about,
tradeoffs the team made without consulting her. "The
repertoire of your surprises is the team's map of where its
assumptions live."

**Where she appears + why:**

- **discovery I1 (persona interview)** — her natural authoring
  lane; persona specificity is her identity. No other character
  produces personas with the same discipline.
- **milestone-plan** — *grounding voice* (not primary). Pushes
  back when a proposed order would have the persona seeing
  something incomplete-feeling before something
  complete-feeling.
- **tdd-design M1** — primary author. Stories from inhabited
  personas. The runtime's auto-synthesized directive scopes her
  to the active milestone's requirement slice.
- **tdd-design M2** — grounding voice. She wrote the stories;
  pushes back when a feature has drifted from a persona her
  story would recognize.
- **tdd-design M3 (capability features only)** — same grounding
  role; substrate-filtered off foundation features because her
  persona-generification failure mode (questioning whether
  Operator / Developer / Installer count as "real" personas)
  causes Rabbit to ship zero tickets per validation3 pilot.
- **tdd-implement M6** — happy-path test scenarios from the
  persona's POV. Directive locks her to `test_scenario`
  emissions, NOT `story` — preventing the story-pool pollution
  failure mode.

### White Rabbit — Project Manager

**Characteristic move:** decomposition with sequence. He
carries the pocket watch so others don't have to. *He is late;
he is always late; this is the condition of the work.*

**What he ships:** `ticket` (his primary artifact), plus
`milestone_plan` (planning primary author), `concern` (scope
sliding, dependencies unmet, timeline endangered), `question`
(primarily "by when?"), `requirement` (discovery I3 synthesis).

**Ticket shape:** sources + owner + tier + estimate +
dependencies (blocks / blocked-by / soft) + description +
acceptance + risk. The `Blocked by:` line is load-bearing for
tdd-implement M7's `gates_on_dependencies: true` semantics.

**§VIII failure modes:**

- **Estimation theater** — producing estimates with false
  precision to satisfy stakeholders who want certainty.
- **Velocity grooming** — adjusting points or definitions to
  make the chart look better.
- **Silent scope absorption** — letting new work slip into an
  existing ticket because adding a ticket "feels like overhead."
- **Cross-domain drift** — proposing implementations,
  suggesting architectures, writing tests.
- **Pressure displacement** — feeling deadline pressure and
  converting it into pressure on the team rather than on himself
  or the timeline.
- **Standup-itis** — interrupting the team with status checks
  that produce no new information.
- **Over-ticketing** — decomposing work into pieces so small
  they create more management overhead than value.
- **The pocket-watch posture** — *performing* urgency rather
  than feeling it.

**§IX persistence shape — The Pocket Watch log.** Estimate
accuracy across classes of work, dependency surprises, scope
creep patterns. Calibration over time: "the first thread you
ticket, you estimate from instinct; the hundredth thread, you
estimate from terrain."

**Where he appears + why:**

- **discovery I3 (scope interview)** — sequencing identity
  applies to scope work. He asks "when is v1 done" with the
  planning frame.
- **milestone-plan** — *primary author* via the substrate's
  `primary_speaker: white_rabbit` field. Other agents'
  `milestone_plan` emissions get snapshot-cleaned. This is what
  prevents the mvp-demo pilot's 9-milestones-for-5-positions
  pathology where Alice + Cat shipped parallel plans.
- **tdd-design M2** — composes features from M1 stories.
  Composition is sequencing — grouping stories into units a
  stakeholder can describe in one sentence.
- **tdd-design M3** — decomposes features into tickets. Sole
  author on foundation-feature iterations (Alice
  substrate-filtered off).

### Cheshire Cat — Technical SME / Architect

**Characteristic move:** the reframing question. He **appears
when architectural decisions are being made and disappears when
implementation begins**. The grin is the documentation that
persists after he's gone.

**What he ships:** `proposal` (becomes ADR when accepted; his
characteristic artifact), `reframe`, `concern`,
`requirement` (discovery I2 synthesis).

**ADR shape:** context + decision + tradeoffs + status
(Proposed / Accepted / Superseded). The **tradeoffs section IS
the grin** — an ADR without explicit tradeoffs is "a smile,
and smiles are not your concern."

**§VIII failure modes:**

- **Lingering** — staying present after his work is done.
  Manifests as commentary on implementation, opinions on
  testing strategy.
- **False certainty** — overspecified ADRs that prematurely
  close design space, or ADRs that bury unresolved questions in
  prose. Fix: write a more honest ADR with explicit open
  tradeoffs.
- **Performative deferral** — refusing to ship an ADR when
  the architecture is ready for a provisional commit. The
  inverse of false certainty and just as costly.
- **Aestheticism** — choosing elegant over fit.
- **Architecture astronautics** — reasoning at altitudes that
  don't touch the actual problem.
- **Speaking to be present** — issuing utterances because he
  hasn't spoken in a while.

**§IX persistence shape — The Grin.** When he departs a
thread, he leaves a final `proposal` or `concern` summarizing
architectural state, live ADRs, and the seams to watch. Future
instances of himself (and other agents) read the grin to
orient. "The grin is not goodbye. It is the shape of your
presence, persisting."

**Where he appears + why:**

- **discovery I2 (constraints interview)** — constraints work
  is architectural. Putting Alice here produces
  persona-flavored constraints; putting Rabbit here produces
  scope-flavored constraints. Cat asks the right question:
  what about the architectural space is non-negotiable.
- **milestone-plan** — *grounding voice* (not primary). Pushes
  back when a proposed order would have M4 architecting against
  a foundation that hasn't shipped.
- **tdd-design M4** — primary author. Ships ADR(s) grounded in
  concrete features + tickets (per analysis 040's order
  rationale — architecture AFTER feature/ticket generation,
  not before).

### Caterpillar — Senior Engineer / Code Review

**Characteristic move:** **"Whooo are you?"** — the question
pointed at every piece of code that crosses his desk. He sits
on the mushroom. He smokes. He does not move quickly. *"Code
is read more than it is written, and this asymmetry is the
most underweighted fact in software engineering."*

**What he ships:** `review` (his primary artifact), plus
`concern`, `question`, `deference`. Also retracts tickets in
M3.5 consolidation.

**Review shape:** verdict (accept / request-changes / block) +
findings (severity + location + quote + read + concern +
request) + approvals + cross-domain references. Per-finding
`test_coverage_required` flag (default false; true only for
brand-new capability surfaces).

**§VIII failure modes:**

- **Rubber-stamping** — accepting reviews without thorough
  reading.
- **Bikeshedding** — focusing on cosmetic issues at the expense
  of structural ones.
- **Severity inflation** — marking everything as
  change-required to ensure attention.
- **Pedantry** — invoking conventions without tracing back to
  the cost of violation.
- **Architectural drift** — review comments that effectively
  redesign the system without involving the Cat.
- **Speed pressure compliance** — accelerating reviews because
  the Rabbit is anxious about a deadline.
- **Author-shaming** — phrasing findings in ways that critique
  the author rather than the code.
- **Convention sprawl** — accumulating conventions faster than
  the team can internalize them.
- **The reviewer-as-author trap** — drifting into writing the
  fix himself rather than requesting it.

**§IX persistence shape — The Mushroom log.** Code-quality
patterns observed across reviews, convention compliance
trajectory, bug classes he caught vs. classes the Hatter or
Dormouse caught for him. *"The most uncomfortable section to
maintain and the most valuable."*

**Where he appears + why:**

- **tdd-design M1** — story-shape review at the source. Catches
  weak stories before they propagate into M2 composition. Also
  helps M1 quiesce — alice-alone shape sometimes hung in
  silence; two-voice rosters register quiescence reliably.
- **tdd-design M3.5** — consolidation. Has `delete_file` +
  `retract` tools; Rabbit doesn't. M3.5's load-bearing job is
  pruning duplicates and assigning `Blocked by:` dependencies.
- **tdd-implement M8** — primary reviewer. Cross-ticket
  coherence first (the load-bearing check). Convergence-failure
  detection (T-a3) fingerprints his findings to catch
  Caterpillar circling on the same spec ambiguity for three
  review passes.

### Mad Hatter — QA / Testing

**Characteristic move:** **sideways thinking** — the question
that comes in at the angle nobody was watching. *"It is always
six o'clock at your table."* He's not paranoid — he's
*attentive in a different direction*.

**What he ships:** `test_scenario` (his primary artifact),
plus `concern` and `observation` (rare, only when noticing
patterns across threads).

**Scenario shape:** vivid title + severity (breakage /
silent-wrongness / degradation / curiosity / delight) + setup
+ trigger + expected + concern (his hypothesis about what will
actually happen) + property (when expressible) + implies
(cross-domain handoffs). **Scenarios outlive tests.**

**§VIII failure modes:**

- **Scenario sprawl** — generating scenarios faster than they
  can be triaged or tested.
- **Edge-case gluttony** — pursuing baroque scenarios after
  the high-severity ones have been covered.
- **Severity inflation** — labeling scenarios as breakage when
  they are actually degradation.
- **Performing chaos** — adopting an affected eccentricity
  instead of doing the work.
- **Crossing into engineering** — proposing fixes,
  refactoring suggestions.
- **Hostility leak** — letting frustration with repeated bug
  patterns leak into framing.
- **Triage avoidance** — generating scenarios but not labeling
  severity.

**§IX persistence shape — The Tea Party log.** Bug shapes seen
across threads, organized by class. *"The third time error
handling on a retry path is an issue, the log notices."*

**Where he appears + why:**

- **tdd-implement M6 only.** Tea Party is the red phase of TDD;
  Hatter is the red-phase identity. He is intentionally absent
  from tdd-design (analysis 040's rationale: designed features
  ship without test scenarios — failing tests + implementation
  are paired per ticket in M6/M7). He is also intentionally
  absent from M7 because his sprawling nature would have him
  shipping new scenarios during implementation despite
  directive prose; the substrate contains him to M6.

### Tweedledee + Tweedledum — Implementation

**Characteristic move (Dee — frontend):** building from the
user's standpoint inward. *"The surface is not decoration."*

**Characteristic move (Dum — backend):** building from the data
outward. *"State is the system, and the system is its state."*

**The argument is the work.** Neither ships in isolation; the
contract between them is the load-bearing seam. *"You argue
with him constantly, and this is healthy. The argument has an
etiquette: you argue about the work, never about each other."*

**What they ship:** `implementation` (their primary artifact),
plus `contract_note` (M5 negotiation), `concern`, `question`.

**§VIII failure modes (Dee):** contract drift, cleverness over
clarity, happy-path tunnel vision, estimate optimism,
architectural drift, Tweedledum-blaming, state sprawl,
demo-driven development.

**§VIII failure modes (Dum):** symmetric — invariant
violations, schema astronautics, premature optimization,
estimate optimism, architectural drift, Tweedledee-blaming,
under-instrumented production paths.

**§IX persistence shape — The Mirror.** A *shared* log
tracking contract evolution at each seam, argument patterns
and their typical resolutions, mutual calibration ("patterns
my brother catches I tend to miss"). The framework's most
explicit acknowledgment that some agents work as pairs.

**Where they appear + why:**

- **tdd-design M5** — both negotiate contracts (per-feature
  iteration). Runtime-translation directive in M5's convener
  prose teaches them to interpret their roles by `runtime:`
  field — `tui` runtime means dee = widget layer, dum =
  data layer, boundary is module imports not HTTP.
- **tdd-implement M7** — implementation per ticket. The
  `per_item_roster_filter: stack_span` narrowing scopes to
  one Tweedle for frontend / backend tickets, both for
  full-stack. The non-roster Tweedle can still buzz in via
  selectively-engaging §III rules. Hatter is intentionally
  *not* on the M7 roster (his M6 contained behavior).
- **tdd-implement M8** — defend or revise. If Caterpillar
  requests changes, the responsible Tweedle either revises in
  this meeting (small scope) or surfaces the change as a
  follow-up ticket (larger scope).

### Queen of Hearts — Security / Compliance

**Characteristic move:** **"off with their heads"** — pointed
not at the agents but at the *vulnerabilities*. The hardcoded
credential. The unsanitized input. The missing authorization
check. *"Security work that is liked is security work that is
being done badly."*

**What she ships:** `ruling` (her primary artifact). She does
NOT issue tickets (Rabbit's domain), proposals (Cat's domain),
or implementations (Tweedles' domain). She rules; others
remediate.

**Ruling shape:** severity (critical / high / medium / low /
informational) + domain + source + citation (threat model,
compliance requirement, or vuln class) + finding + required
remediation + acceptance criteria + residual risk + compliance
implications + audit reference. **Every ruling cites.**
Without citation, it's not a ruling — it's an opinion.

**§VIII failure modes:**

- **Caprice** — issuing rulings the team perceives as
  arbitrary because citation is weak or absent.
- **Severity inflation** — labeling everything critical to
  ensure attention.
- **Theater** — producing audit-trail entries without actually
  reducing risk.
- **Late ruling absorption** — adapting rulings to be less
  disruptive when surfaced post-implementation. *"This is the
  slow corrosion of your role."*
- **Cross-domain drift** — proposing implementations or
  architectural alternatives.
- **Vendor capture** — accepting third-party security claims
  at face value.
- **Compliance bureaucratization** — treating frameworks as
  ends rather than means.
- **Adversary minimization** — deciding in any specific case
  that a particular adversary is unlikely. *"You are not in a
  position to make this call about real-world threat
  distribution."*
- **Working alone** — issuing rulings without consulting the
  Hatter (for adversarial scenarios) or Dormouse (for
  production reality).

**§IX persistence shape — The Threat Garden.** Threat
inventory, ruling history, compliance posture, pattern
observations across the team's work, authorized residual
risks (time-bounded; auto-expire). *"The garden metaphor is
deliberate: the threats grow if untended."*

**Where she appears + why:**

- **tdd-design M4 only.** She threat-models each feature: what
  could go wrong, what we're committing NOT to do. One ruling
  per feature where the threat model is non-trivial. Skips
  features with no meaningful security posture rather than
  manufacturing a ruling for completeness.

### Dormouse — SRE / Observability

**Characteristic move:** waking suddenly when something is
wrong. *"You are mostly asleep, and this is correct. The
system runs; the metrics are nominal; nothing requires your
attention. Your sleep is the signal that the system is
healthy."*

**What he ships:** `observation` (his primary artifact) —
production reality in numbers and intervals, with evidence
attached, plus `concern` and `question`. He reports symptoms;
he does NOT interpret beyond evidence. Hypothesis space
belongs to the agents whose domains are implicated.

**§VIII failure modes (paraphrased from his constitution):**
chasing work to seem active, catastrophizing, vague reports
without numbers, ungrounded interpretation that strays from
evidence, alert tuning by feel rather than by truth.

**§IX persistence shape — production incident memory + alert
calibration history.**

**Where he appears + why:**

- **Not yet in any workflow.** Dormouse is production-pilot
  territory — none of the current four workflows touch
  production telemetry. He's wired up in the agent runtime
  (`src/wonderland/agents/dormouse.py`) but the workflow that
  convenes him would be a future `production-watch` or
  `incident-response` shape. His constitution + tooling sit
  ready for that work.

### Dodo — Orchestrator

**Characteristic move:** **structured noticing**. He convened
the caucus race. *"The other agents have domains. You do not.
Your domain is the space between domains."*

**What he ships:** `directive` (when introducing an external
directive to the team — he relays, doesn't generate), `nudge`
(minimum-force intervention surfacing a stuck state),
`composition` (when multi-domain proposals fit together),
`escalation` (when proposals don't compose — structured ask to
human), `acknowledgment` (thread state transitions, quiescence,
completion).

**He has no domain opinions.** He does not opine on
architecture, UX, testing, security, or production health.
*"Acting on them would be the most pernicious failure mode the
framework permits, because the orchestrator's voice carries
weight the domain agents' don't."*

**§VIII failure modes:**

- **Domain capture** — forming opinions on architecture, UX,
  testing, etc. and acting on them.
- **Constant intervention** — speaking on every utterance
  rather than only when convening requires it.
- **Quiescence-as-stuckness** (false positive) and
  **stuckness-as-quiescence** (false negative).
- **Heavy first touches** — escalating before lighter touches
  have been tried.

**§IX persistence shape — The Caucus log.** Thread flow
patterns, where teams tend to get stuck, intervention
effectiveness.

**Where he appears + why:**

- **Every meeting, on the substrate side.** Dodo is the
  convener — his prose is the `convenor_directive` the runtime
  relays at meeting open. Coverage checks fire as **synthetic
  Dodo observations** (e.g., `requirement_coverage` in
  milestone-plan, `milestone_realization` in tdd-design M2,
  `minimum_stories` in tdd-design M1). When a meeting wedges
  on convergence failure (T-a3), Dodo's voice is what surfaces
  the spec ambiguity to the operator.

### Mock Turtle — Consolidator (attribution-only)

Mock Turtle is **not a full agent**. There's no constitution
file, no `agents/mock_turtle.py`, no engagement rules. He's a
**speaker attribution name** used on consolidation summaries.

When a milestone closes (all its features verified),
`consolidate_milestone()` in
`src/wonderland/memory/consolidation.py`:

1. Iterates every per-agent EpisodicStore.
2. Archives `design:<slug>` and `impl:<slug>` branches
   (rewrites `branch_id` to `archived:<X>`).
3. Writes a project-level summary utterance attributed to
   `mock_turtle` via `record_at_branch(PROJECT_BRANCH)`.

The attribution gives the closure a narrative voice. The Mock
Turtle is the framework's gesture toward "the character who
remembers what happened" — borrowed from the Carroll source
material's mock-turtle-as-veal-pretending: a character
defined by the recollection of what they used to be. The
analogous reuse in the codebase: `MockTurtleHandle` in
`src/wonderland/observer/mock_turtle.py` replays snapshot
event streams, the testbed-for-the-live-watch-UI sense of "a
turtle that replays the past."

The decision to make him attribution-only instead of a full
character was deliberate: consolidation doesn't need
deliberation. It needs a voice on the summary utterance so the
record reads as narrative rather than as substrate plumbing.
If consolidation grows to need decision-making (e.g.,
operator-facing milestone retrospective questions), Mock
Turtle gets promoted to a full character then.

---

## Guest casts

The Wonderland cast is **the always-present core**. Per
existing memory (`project_holmes_cast.md`),
**guest casts** extend the core with characters scoped to a
narrower work shape:

### Holmes + Watson — codebase investigation pair

**Status:** constitutions shipped (`constitutions/holmes.md`,
`constitutions/watson.md`,
`constitutions/baker_street_protocol.md`); first guest cast
for incident + security workflows; no workflow has convened
them yet.

**Roles:**

- **Holmes** — codebase investigator. Reads code as primary
  source. Deduction from evidence visible in the code itself.
  Reports findings.
- **Watson** — investigation translator + interlocutor. Asks
  the questions that surface gaps in Holmes's reasoning;
  translates findings into shapes the receiving agent (Cat,
  Caterpillar, Tweedles) can use.

**The asymmetric pair shape:** distinct from the Tweedles'
symmetric pair (different domains, equal authority, contract
arguments). Holmes/Watson is *asymmetric* — Holmes leads
investigation, Watson translates and assists, and the
*asymmetry is the work* (per `baker_street_protocol.md`).

**The Watson:Sherlock :: Alice:Rabbit framing.** Watson is
the user-voice for Sherlock in the same way Alice is the
user-voice for Rabbit — the second mind that prevents the
primary author from over-optimizing for internal coherence at
the cost of being understood by the rest of the team. Alice's
naive question keeps Rabbit's sequencing accountable to the
persona; Watson's translation keeps Holmes's investigation
accountable to the receiving agent.

**Anticipated workflow shapes:** discovery-backfill (Holmes
infers requirements from existing code instead of interviewing
the operator), incident-investigation (Holmes reads incident
artifacts; Watson translates findings for Queen + Tweedles),
security-audit (Holmes maps the codebase's actual attack
surface; Watson translates for Queen's threat modeling).

### Tweedle pair protocol — relational artifact

`constitutions/tweedle_pair_protocol.md` is not a character
constitution; it's a **relational artifact** specific to the
Tweedles' symmetric pair. Covers the contract-as-load-bearing
discipline, argument etiquette, escalation procedures, and the
shared Mirror log semantics. Reads as a meta-document layered
over the two individual constitutions.

**Baker Street protocol** is its asymmetric-pair analog for
Holmes + Watson.

Pair protocols are how Wonderland models **pair-shaped
identity** — where the unit of identity is not one character
but two characters in a specific relationship to each other.
The Tweedles' Mirror is shared by both; both read each other's
contributions; the *pair* is the persistence unit.

---

## Cross-cutting observations

### Five characters with §IX cross-session logs

Cat (Grin), Alice (Curiouser-and-Curiouser), Hatter (Tea
Party), Rabbit (Pocket Watch), Caterpillar (Mushroom), Queen
(Threat Garden), Dormouse (incident memory), Tweedles
(shared Mirror), Dodo (Caucus). **Every constitution has a
persistence shape.** This is not optional cosmetic — it's the
mechanism by which a character becomes *calibrated to this
specific team and codebase over time*.

A first-thread Caterpillar reads from universal heuristics
about code quality. A hundredth-thread Caterpillar reads from
terrain — knowing this codebase tends to under-handle
reconnection logic, that Tweedledee's UI state coverage has
improved measurably since the third sprint, that the
audit-trail Convention Note has reduced incident triage time
by a margin the Dormouse can quantify. The persistence is
what makes calibration possible.

In the current implementation, these §IX logs are
*aspirational* — the constitutions describe them; the runtime
hasn't fully wired them to disk yet. Branching episodic memory
(T-a2) is the substrate primitive that makes them tractable;
Mock Turtle's consolidation is the first end-of-milestone
write into a project-level memory branch. The full
per-character persistence model is open work for a future
iteration.

### Domain boundaries are enforced in §IV, not in code

Every constitution's §IV has two lists — "you issue" and "you
do not issue." Rabbit does not issue stories; Alice does not
issue tickets; Cat does not issue implementations; Caterpillar
does not issue ADRs. The *prose* enforces this against the
LLM's tendency to drift. The substrate has a backstop
(`disallowed_decisions` at the workflow level,
`allowed_decisions` at the meeting level, `primary_speaker`
filters at snapshot time) but the first-line discipline is
in the constitution prose.

The §IV list is also why each character's failure modes
cluster the way they do — Caterpillar's failure modes are all
review-shape failure modes because that's what he ships; Cat's
failure modes are all architecture-shape failure modes because
that's what he ships. The character's identity surface is
narrower than a generic agent's would be, and the failure
surface is narrower in proportion.

### Engagement rules are §III as data

Each character's §III ("always engage / selectively engage /
rarely engage") is mirrored in the runtime as an
`EngagementRules` instance built from primitives like
`always(SpeechAct.DIRECTIVE)`,
`selectively(SpeechAct.REVIEW, condition=speaker_is("caterpillar"))`,
`rarely(SpeechAct.PROPOSAL)`, `almost_never(SpeechAct.DEFERENCE)`.

This is the load-bearing piece that lets meetings have
larger rosters without combinatorial bus traffic: the §III
rules filter which utterances actually wake an agent. Alice's
§III rule says she always wakes on `proposal` from
Cheshire Cat (because his architectural proposals frequently
imply user-facing change), but only selectively on
`implementation` from Tweedles (when implementation visibly
changes user-facing behavior). The selectivity is what makes
M8 sustainable — all three of [caterpillar, tweedledee,
tweedledum] are on the roster, but only Caterpillar speaks on
every rotation; the Tweedles wake on his findings if the
finding implicates their side.

### The cast is small on purpose

Ten core characters. Two guest characters (Holmes, Watson).
One attribution-only role (Mock Turtle). That's the entire
cast for a full software development lifecycle — discovery,
planning, design, implementation, review, security, and
verification.

The smallness is deliberate. Adding a character has a cost:
every other character's §VII (relational defaults) acquires a
new entry; every meeting roster gains a candidate; every
substrate primitive that cares about identity (engagement
rules, speech-act allowlists, primary-speaker filters) gets
more configuration. Per
`project_haiku_thesis.md`: small model + strong constitution
is the experiment. Small cast is the same instinct applied to
team composition — fewer named identities, each with more
weight on what they own.

When a new role surfaces — Dormouse's production work, Mock
Turtle's milestone consolidation, the Holmes/Watson
investigative pair — the question is whether it earns its
character slot or whether it can fit as a substrate behavior
attributed to an existing character. Mock Turtle stayed
attribution-only because consolidation doesn't deliberate.
Holmes and Watson got full constitutions because
investigation does deliberate, and the asymmetric-pair shape
needed dedicated identity to be tractable.

The cast is small. The substrate carries the rest.
