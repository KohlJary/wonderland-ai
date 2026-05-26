# §3 — Architecture: how Wonderland actually runs

## §3.1 — Reader's guide

Wonderland's pipeline runs the full software-development
lifecycle in four atomic workflows that an operator composes
in order:

1. **discovery** — interview the operator; capture intent as
   `requirement` artifacts on disk.
2. **milestone-plan** — group requirements into an ordered
   trajectory of `milestone` artifacts.
3. **tdd-design** — for a given milestone, produce stories →
   features → tickets → architecture → contracts.
4. **tdd-implement** — for queued features, write failing
   tests, implement against them, review the cohesive
   deliverable, and verify by actually running the project's
   test suite.

Each workflow is a YAML file that declares meetings (or
interviews in discovery's case), a roster per meeting, a
sequence of phases per meeting, exit conditions per phase,
and bookkeeping about how the substrate transitions
lifecycle state. Workflows are intentionally short — the
longest is ~800 lines of YAML, half of that being prose
directives the runtime relays to the agents. The substrate
enforces the rest.

The cast referenced throughout (developed in detail in §4):

- **Alice** — user-voice; persona-anchored grounding.
- **Caterpillar** — coherence reader; reviews artifacts
  against bus + disk for citation integrity.
- **Cheshire Cat** — architect; owns ADRs with named
  tradeoffs.
- **White Rabbit** — planner; owns sequencing,
  decomposition, composition.
- **Tweedledee + Tweedledum** — implementers (frontend bias /
  backend bias); pair-protocol negotiation on contracts.
- **Mad Hatter** — adversarial test designer.
- **Queen of Hearts** — security lens.
- **Mock Turtle** — milestone-closeout consolidator.
- **Dodo** — orchestrator; substrate-injected nudges.

### Substrate primitives the workflows lean on

- **roster** — who can speak at this meeting.
- **convenor_directive** — prose framing the runtime relays
  to the roster at meeting open.
- **allowed_decisions** — substrate-level allowlist on
  artifact shapes; emissions outside the list get stripped.
- **primary_speaker** — when multiple agents could ship the
  same artifact kind, the primary's emission survives
  snapshot.
- **phases** — meetings break into ordered phases with their
  own rotation caps and exit conditions.
- **exit_condition_artifact** — phase ends as soon as one
  agent ships an artifact of this kind.
- **per_item** — iteration unit (`per_item: feature` runs
  the meeting once per feature in scope).
- **iterate_only_in_states** — lifecycle gate: skip
  iteration items not in this list of states.
- **gates_on_dependencies** — within a parallel level,
  iteration items wait for their `Blocked by:` upstreams.
- **coverage_check** — substrate runs a check at end of
  rotation; on failure, injects a synthetic Dodo observation
  and grants a bonus rotation (capped).
- **seeds** — declarative spec for what utterances + on-disk
  artifacts the meeting can see.
- **transition_iteration_to** — lifecycle state the
  substrate transitions the iteration item to when the
  meeting closes successfully.

The remainder of this chapter walks three meetings in
detail to show the engineered-friction mechanism at work:
**discovery's three-interviewer structure** (each lens
shapes its own interview), **tdd-design M5** (the canonical
pair-protocol negotiation), and **tdd-implement M8** (the
canonical multi-lens review). Appendix A walks every other
meeting in every other workflow at the same granularity.

---

## §3.2 — Discovery: three lenses, three interviews

Discovery is the operator's first contact with the system
on a fresh project. Three short focused interviews run in
series; each captures operator answers as `requirement`
artifacts on disk under `.wonderland/requirements/`. There
are no meetings here — discovery is interview-only. The
operator answers ~12 minutes of questions; the substrate
writes ~15-25 requirement files; downstream workflows seed
from those files instead of re-prompting.

### Why three interviewers instead of one

Each character's interview shape matches their lens. Alice
asks about people; Cat asks about constraints; Rabbit asks
about scope boundaries. Mixing those into a single
interviewer either drops quality (one voice trying to cover
three frames) or pads the operator's load (asking
everything but treating answers uniformly). **Splitting is
the architecture choice that operationalizes the multi-lens
commitment at the discovery layer.**

The interviewers don't talk to each other during
discovery. There is no shared deliberation — each interview
is operator ↔ interviewer one-on-one, and the requirement
artifacts get composed in the next workflow
(milestone-plan) by a different roster.

### I1 — Persona interview ("Who is this for?")

- **Interviewer:** Alice
- **Goal:** capture personas + situations that anchor
  downstream design

**Why Alice:** persona work is Alice's identity. Her
constitution trains for specificity in personas — "Maya, 31,
polyglot moderator at a translation startup, end of day,
scrolling through 40 pending threads" beats "the user."
Putting any other character here produces generic personas
that drift into stack-talk or scope-talk.

**Output shape:** Alice synthesizes each answer into one or
more `persona` or `situation` requirements with stable
slugs. The deferred-personas answer becomes one or more
`persona` requirements with `tier: deferred` (so downstream
M2 composition can see them as explicitly-deferred rather
than re-introducing them into v1 scope).

### I2 — Constraints interview ("What can't move?")

- **Interviewer:** Cheshire Cat
- **Goal:** surface technical constraints, integrations, and
  deal-breakers

**Why Cat:** constraints work is architectural. Cat's
constitution trains for architectural sensitivity — what
bounds the solution space before he proposes anything.
Putting Alice here produces persona-flavored constraints
("Maya needs it fast"); putting Rabbit here produces
scope-flavored constraints ("we need it by Tuesday"). Cat
asks the right question: what about the architectural space
is non-negotiable.

**Output shape:** Cat ships `constraint`, `integration`,
and `deal_breaker` requirements. The deal-breakers
requirement kind is load-bearing — downstream M4
(architecture) reads it to know what tradeoffs are off the
table.

### I3 — Scope interview ("When are we done?")

- **Interviewer:** White Rabbit
- **Goal:** pin down success criteria + explicit
  out-of-scope

**Why Rabbit:** scope is a sequencing question and Rabbit
owns sequencing. He asks "when is v1 done" with the
planning frame ("what does shipped mean") rather than the
persona frame ("would Maya be happy") or the architecture
frame ("did we build the right system"). Out-of-scope is
its own load-bearing artifact kind — naming features the
team might propose but you want to defer prevents M2 from
silently composing them in.

**Output shape:** Rabbit ships `scope`,
`success_criterion`, and `out_of_scope` requirements.

### The discovery argument

Three lens-distinct interviews capture grounding (personas
+ situations), bounds (constraints + deal-breakers), and
ship-criteria (scope + success criteria) as **separately
typed** artifacts. Subsequent workflows can read each kind
independently — milestone-plan reads `success_criterion` to
know what observables mean a milestone is done;
tdd-design M4 reads `deal_breaker` to know what
architectural tradeoffs are off the table. The lens split
isn't stylistic; the typing makes each kind individually
addressable downstream.

This is the architectural pattern the rest of the substrate
generalizes: **separately-typed artifacts produced by
lens-distinct identities, composed downstream through
substrate-level invariants.**

---

## §3.3 — tdd-design M5: contract negotiation as engineered friction

The canonical pair-protocol meeting. M5 negotiates per-feature
contracts informed by the architectural commitment from M4.
**This meeting demonstrates the friction-as-substrate
mechanism more concretely than any other.**

- **Roster:** Tweedledee, Tweedledum, Alice
- **Per-item:** feature
- **Parallel:** true (feature-level contract negotiation is
  independent)

### Why both Tweedles

The seam between frontend and backend is **negotiated, not
unilateral**. Contract notes name what shape the team is
committing to — function signatures + dataclasses for
in-process, endpoints + envelopes for HTTP. Both sides see
the contract and either confirms or pushes back.

The pair-protocol shape is constitutive: neither Tweedle
ships a contract in isolation. The substrate enforces the
team_groupings (`[[dee, dum, alice]]`) to ensure both are
present.

### Why Alice on the roster

Grounding voice. She pushes back when a contract compresses
the user-facing point of a feature past recognition, OR when
a contract drifts from the runtime shape (HTTP language in a
TUI project, etc.). Default to silence; engage when a seam
decision threatens a story Alice's persona would recognize
OR threatens the runtime fact in project_context.

This is the **third-lens-on-pair** pattern that recurs at
M6 (Hatter pair with Alice grounding) and M8 (Caterpillar
pair with both Tweedles for defend/revise). The pair's
output gets read through a third lens whose failure mode is
*different* from either pair member's failure mode. Two
voices in symmetric contract negotiation; the third voice
in user-recognition grounding.

### Runtime-translation directive

The Tweedles' role names ("tweedledee = frontend bias",
"tweedledum = backend bias") describe a division of labor
that interprets **differently** in different runtimes. The
convenor directive translates:

- `runtime: tui` — dee = widget/screen/layout; dum =
  data/model/persistence. Boundary is module imports, not
  HTTP.
- `runtime: cli` — dee = argparse/output formatting; dum =
  subcommand logic + persistence. Same in-process rule.
- `runtime: web` — dee owns browser surface; dum owns API
  service; boundary IS HTTP.

The constitutions stay constant; the runtime field reshapes
how the roles interpret in this project. This is what lets
the same ten characters compose into TUI, CLI, and
fullstack projects without per-runtime constitution
variants.

### Phases

| Phase | Max rotations | Exit condition |
|-------|---------------|----------------|
| `discussion` | 2 | `contract_note` |
| `commit` | 1 | `contract_note` |

**Transition:** `transition_iteration_to: designed` — each
feature transitions `in_design → designed` on successful
contract negotiation. Designed features are eligible for
tdd-implement once the operator queues them.

### What this meeting demonstrates architecturally

The friction here is engineered. Neither Tweedle ships a
contract alone (substrate-enforced); both must see the
seam; Alice grounds when persona-recognition is
threatened. The output (contract notes with proposed_change
+ current_shape + rationale) carries the receipts of all
three perspectives, not just one. **The architectural
choice that produces production-shaped contracts is putting
both pair members AND the grounding lens in the same
meeting with substrate-enforced roster discipline.** No
single agent could produce the contract shape; the
juxtaposition is what does the work.

---

## §3.4 — tdd-implement M8: single-lens review with forced citation

The canonical single-participant meeting in the substrate.
**Schema-as-safety (§7 Pillar 3) depends on this meeting's
structural discipline; convergent self-repair (§7 Pillar 4)
lives in Caterpillar's read-the-code-fresh discipline here.**

- **Roster:** Caterpillar (solo, post-T-ab54)
- **Per-item:** feature

### Why Caterpillar solo

Review is coherence reading and that's Caterpillar's
identity. He reads the cohesive deliverable — not just
individual files but the relationships between them. His
constitution's §VIII (rubber-stamping, severity inflation,
pedantry, author-shaming, reviewer-as-author trap) is the
register the substrate counts on him to operate within.

M8 wasn't always single-participant. The mvp pilot ran
Caterpillar + both Tweedles on the roster — defend-or-revise
in the same meeting. Telemetry on the obol-260522 pilot
(detailed in `caterpillar-m8-cost-analysis.md`) surfaced
that Tweedles paid full per-call cache-creation cost for each
M8 window while engaging substantively in only ~20% of them;
their other 80% was silence-overhead. T-ab54 narrowed the
roster to Caterpillar solo. The redux pilot validated: M8
spend dropped from ~30% of total to ~11%, with no
review-quality regression in subsequent adversarial Theseus
review.

### Single-participant meetings as an architectural pattern

M8's roster narrowing is the canonical example of a broader
substrate principle: **single-participant meetings are an
allowed and sometimes-correct configuration**. The default
multi-agent assumption — more voices produce better outputs
through friction — is true for meetings whose output emerges
from inter-agent negotiation (M5 contract negotiation is the
canonical multi-participant case). But review-class meetings
whose output is one identity's coherent read of a deliverable
benefit from solo execution: the friction with other voices
would be deliberation-overhead, not constraint-encoding.

The substrate's roster discipline is content-aware, not
formula-driven. The Tweedles can still buzz in via §III
selective engagement when a contract question surfaces
mid-review — they're not on the standing roster but they're
not silenced from the conversation either. The substrate
distinguishes "primary author of the verdict" from "may
participate when their domain is invoked." M8 has one
primary author and zero standing-roster co-participants;
that's the configuration the data drove the substrate to.

### Cross-ticket coherence first (the load-bearing check)

Per analysis 040 (referenced for the order-rationale
finding), the most expensive defects in feature work live
*between* files. A contract note says one thing; the
backend implements 50% of it; the frontend assumes 100% of
it. Or a component gets built but never wired into the app
entry point. Per-file reviews can't catch these — they
require reading multiple files together. The convenor
directive enumerates the order:

1. **Cross-ticket coherence FIRST.** Open these together
   BEFORE any single-file review: the feature's contract
   note(s), at least one backend file the contract names,
   at least one frontend / consumer file the contract
   names, the app entry point. Verify: do all three name
   the same fields with the same semantics? Does the app
   entry point actually import and render the component the
   work produced, or is it still rendering the skeleton's
   placeholder UI? **Contract drift and orphaned components
   are the canonical cross-ticket bugs.**
2. **Does the code match the contract?** Per-file walk
   against ADR + contract notes.
3. **Do the tests cover the acceptance criteria?**

If budget runs out partway through, the cross-ticket check
(#1) is the one that has to ship.

### Schema-as-safety: the review finding's required shape

The `ReviewFinding` Pydantic schema requires `location` +
`quote` + `read` + `concern` + `request`. Each finding ships
with these fields populated; the substrate's emission path
rejects findings missing any. **This is what makes
hallucination structurally harder than honest reading on
small models** — a Haiku-class model that tries to fabricate
"this function on line 47 has a race condition" has to also
fabricate the quote, the read context, the file location,
and have them coherently support each other. The shape
forces the agent to actually open the file.

Across 5+ pilots on Haiku 4.5, zero hallucinated findings
have been observed (§7 Pillar 3 develops the receipt).

### Convergence-failure detection

If Caterpillar's findings on the same feature surface the
same fingerprint (file_location +
normalized_concern_first_60_chars) across 3 consecutive
review passes, the substrate detects convergence failure
and writes a spec ambiguity artifact to
`.wonderland/spec-ambiguity/`. The class of bug is
"Caterpillar keeps finding the same thing because the spec
is ambiguous"; surfacing the ambiguity to the operator
beats spinning on review rotations.

This is one of the substrate's structural invariants that
encodes a methodological observation: when the same agent
makes the same finding across multiple passes, the agent
isn't the problem — the spec is.

### Verdict shape

- `accept` (ship it, transition tickets DONE; feature rolls
  up to `ready_for_review`)
- `request-changes` (block, name what must change; tickets
  ABORTED + follow-up tickets synthesized)

### What this meeting demonstrates architecturally

Three architectural pieces visible together here:

1. **Forced citation** as schema-level safety against
   hallucination (the ReviewFinding shape)
2. **Cross-ticket coherence first** as the priority that
   reflects where actual bugs live (between files, not
   within them)
3. **Convergence-failure detection** as a substrate-level
   recognition that some failure modes are spec-level, not
   agent-level

Together these make M8 the meeting that operationalizes
multiple paper claims at once. Schema-as-safety (§7
Pillar 3), multi-lens identity-anchored review (§7
Pillar 2), and convergent self-repair (§7 Pillar 4) all
have receipts that route through this meeting's
structural discipline.

---

## §3.5 — What this chapter establishes

Three meetings, three architectural patterns:

- **Lens-distinct identities → separately-typed artifacts**
  (discovery: each interviewer produces a different
  requirement kind; downstream consumption reads each kind
  independently)
- **Pair + grounding lens → engineered-friction output**
  (M5: pair negotiates contract, third lens grounds
  user-recognition; no single agent could produce the
  output shape alone)
- **Multi-lens review under forced-citation schema →
  hallucination-resistant + cross-cutting-bug-catching
  reviews** (M8: cross-ticket coherence first, ReviewFinding
  schema, convergence-failure detection)

These are representative, not exhaustive. The remaining
~15 meetings across discovery, milestone-plan, tdd-design,
and tdd-implement carry similar architectural choices —
roster discipline matching the meeting's job, substrate
invariants enforcing what the prose framing requests, exit
conditions tuned to the failure mode the meeting most
needs to avoid. Appendix A walks each in the same detail
this chapter walked discovery / M5 / M8.

The chapter's architectural claim, distilled: **Wonderland's
substrate enforces what its convenor directives request.**
Prose tells the agents what to do; substrate refuses to
admit emissions that violate the request. The two together
produce work shapes neither could produce alone, and
neither (substrate enforcement on generic agents OR
constituted agents without substrate enforcement) would
produce on its own. §6 develops the substrate-side
iteration history; §4 develops the agent-side constitutional
patterns; the unified claim §2 names is what they compose
into when they meet at the meeting-level architecture
this chapter walked.
