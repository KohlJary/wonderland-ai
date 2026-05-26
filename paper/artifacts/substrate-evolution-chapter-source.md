# §6 — Substrate evolution

## §6.1 — Why this chapter exists

A paper that says *"we built a multi-agent substrate that ships
production-shaped code on Haiku at single-shot-baseline cost"*
invites an obvious question from a skeptical reader: **how did
you get there?** Multi-agent systems are well-known to be
finicky. The literature is full of demos that work in the
sandbox and fall apart under real workloads, of architectures
that look principled in the diagram and degrade unpredictably
in production. A two-pilot cost trajectory on the same notebook
spec reads as either a measurement artifact or a real
architectural win, and the reader has no way to tell which
without seeing the substrate evolve.

This chapter is the answer. It documents — concretely, with
named substrate fixes, named pilots, named failure modes — the
iteration cycle that produced the trajectory. The story is the
methodology: each substrate primitive shipped is a falsification
of a prior assumption, validated by the next pilot, generating
the next failure to fix. The chapter's load-bearing claim is
not that any individual fix is brilliant; it's that the
**iteration cycle is itself the architectural finding**.

The corollary that frames this whole chapter — Corollary 6,
substrate constraint amplifies identity — predicts that the
substrate should get better as it gets more opinionated.
Conventional wisdom says the opposite: rigid constraints box
LLMs in, leave them brittle, make them worse at edge cases.
The substrate-evolution arc is the empirical refutation of
that wisdom at scale, watched in slow motion across two
pilots and ~60 substrate fixes.

## §6.2 — The pattern

Every substrate fix in Wonderland's history follows the same
shape:

1. **A pilot runs.** Either an experimental harness, a Tier 1
   workflow exercise, or a full Tier 2 autonomous build.
2. **The pilot exposes a gap.** Usually surfaced as either
   (a) a cost spike with no apparent cause, (b) an output that
   passes per-layer checks but fails operator inspection,
   (c) a failure mode that recurs across multiple workflows
   despite ostensibly being fixed before.
3. **The gap gets diagnosed as a substrate-level invariant
   violation.** Some structural property the substrate should
   have been enforcing — milestone scope, citation chain
   integrity, memory isolation, end-to-end composition —
   wasn't actually being enforced.
4. **A substrate fix ships.** Typically <100 lines of code,
   often <30. The fix encodes the missing invariant
   structurally, so the substrate can never again admit a
   transition that violates it.
5. **The next pilot validates** the fix and exposes the next
   gap. The cycle repeats.

This pattern is observable across every substrate fix from
T-v1 (verification substrate) through T-ab64 (end-to-end
composition gates). The fixes are not made by reasoning at
the agent level (*"the Caterpillar should be more careful"*);
they are made by reasoning at the substrate level (*"the
substrate should refuse to admit Caterpillar's review
artifact if its findings don't cite real code at real
file:line locations"*). The agent's grammar narrows; the
substrate's invariants accumulate; the system's coherence
compounds.

A second pattern, less obvious but more load-bearing, is the
**operator-in-loop falsification mechanism.** Substrate gaps
that pass automated checks are still surfaced by the operator
running the system in earnest. The operator notices that a
"verified" feature isn't actually deployed correctly, or that
an apparent cost win came with an output regression, or that
a milestone marked "done" produced code that doesn't compose
end-to-end. Each operator-noticed gap becomes the next
substrate fix. The operator is not an adversarial reviewer
checking for nitpicks — the operator is the falsification
layer the automated checks can't replace. **Without the
operator running pilots in earnest, the substrate's gaps
remain hidden behind passing tests.** With them, every gap
that affects shipped behavior eventually surfaces.

Both patterns compose. The substrate gets opinionated; the
operator falsifies it in earnest; gaps surface as the
operator notices them; fixes encode the missing invariants
structurally. Across enough iteration cycles, the substrate
accumulates a stack of structural invariants comprehensive
enough that the operator can step back and trust the
substrate to catch what they would have caught manually.

The four phases below trace this arc concretely.

---


## §6.3 — Phase 1: Foundational primitives (pre-mvp)

Four substrate layers shipped before mvp ran: the **interview
substrate** (six tasks T-i1 — T-i6) crystallizing operator
descriptions into typed `RequirementPayload` artifacts via
three structured interviews; the **milestone substrate**
(eight tasks T-m1 — T-m8) introducing milestones as first-class
typed artifacts with `done_when`, `consumes_requirements`, and
`kind` fields; the **verification substrate** (seven tasks
T-v1 — T-v7) wiring `build_check` checks that run real shell
commands (pytest, npm build) and feed structured findings back
into the substrate's typed state; and the **GUID identity layer**
(six tasks T-g1 — T-g6) making citation chains drift-proof
under artifact mutation by tagging every artifact with a stable
GUID.

These layers established the typed-state machine the iteration
loop would later harden — requirements (durable, axis-tagged),
milestones (kind-tagged, with done-when), stories/features/
tickets (lifecycle-tracked, citation-chained), implementations
and reviews (artifact-emitted, GUID-anchored), verify gates
(pytest, npm build, with structured findings).

mvp ran on this foundation and shipped a working app for
$83.78. The very act of running it surfaced ~28 substrate gaps
the foundation didn't cover. Those became the input for
Phase 2.

---

## §6.4 — Phase 2: First-pilot hardening (T-ab1 — T-ab28)

mvp was the first end-to-end autonomous Tier 2 pilot. The
operator gave the substrate the notebook directive (~80 lines
of operator-written specification covering capabilities, stack
constraints, non-goals, and success criteria; see
`src/wonderland/closet/directives/notebook.yaml` in the repo)
and let the agents run through discovery, milestone planning,
design, and implementation across three milestones
([analysis 034](https://github.com/KohlJary/wonderland-ai/blob/main/src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md)).
Telemetry, post-pilot analysis, and operator-noticed pattern
recognition together surfaced ~28 distinct substrate
weaknesses. Each became a T-ab task.

The dominant pattern across Phase 2's fixes is **milestones
becoming structurally load-bearing**. The foundational
substrate had shipped milestones as typed artifacts; the pilot
revealed that "the agents read milestones" was not enough.
The substrate needed structural invariants that forced the
agents to actually USE the milestone scope rather than treating
it as ambient context. Four fixes carry the load:

**Foundation/capability axis** (T-ab6, T-ab13, T-ab15) added
`kind: foundation | capability` as a typed field on milestones
with design-phase roster narrowing by kind (Caterpillar solo
for foundation, Alice solo for capability). Closed mvp-demo's
M1-overshoot pattern where the agents shipped backend +
frontend + tests for all three milestones in one pass because
no kind distinction existed.

**Per-milestone memory branching** (T-ab8) introduced distinct
episodic memory namespaces keyed by active milestone. New
milestones start with clean memory; old branches still exist
for retrieval but don't pollute fresh deliberation. This was
the **load-bearing Tier 2 autonomy unlock** — without it, the
substrate could ship M1 cleanly but couldn't ship M2 without
operator memory-clearing. The architectural insight: substrate
damage to typed state self-repairs (Pillar 4); substrate damage
to episodic memory doesn't, and branching at milestone
boundaries is the architectural fix.

**Story-layer milestone scoping** (T-ab9 + T-ab48) added the
milestone seed filter (M2 design seeded only with M2-tagged
requirements/stories/features) plus the write-time validator
(Alice's story emission rejected at write time if milestone tag
doesn't match active scope).

**Tools write-guard** (T-ab12) added perimeter enforcement —
agents can read substrate paths but cannot write to them via
file manipulation tools out-of-band. Without it, agents had
unauthorized write paths that bypassed lifecycle invariants.

Phase 2 also shipped many smaller fixes (iteration efficiency
filters T-ab16-T-ab19, memory recall budgeting T-ab24a/b/c,
review scope discipline T-ab20-T-ab21, per-phase memory scope
T-ab25a, verify finding attribution T-ab26-T-ab28) that filled
out the corners of the substrate without exemplifying the
milestone-as-load-bearing theme as cleanly. The architectural
insight from the cluster: **the substrate enforces what its
convenor directives request** — prose tells the agents what
to do; the substrate refuses to admit emissions that violate
the request.

The next pilot (obol-260522, the CRM project) ran on this
hardened substrate.

---

## §6.5 — Phase 3: Cross-milestone bleed closure (T-ab29 — T-ab53)

obol-260522 was the first Tier 2 pilot on the post-mvp
substrate. It built a CRM project across 4+ milestones,
much larger scope than mvp's notebook. The pilot
shipped at $92.64 — 11% more than mvp — which was
surprising on a hardened substrate. Cost-driver analysis
revealed the substrate's invariants were leaking on a class
of bug that the Phase-2 fixes had partially patched but
not fully closed: **cross-milestone bleed**.

### The bleed pattern across pilots

The pattern: an agent working on milestone N could read
artifacts from milestone N+1 (forward-bleed) or milestone
N-1 (backward-bleed), causing the agent's deliberation to
include out-of-scope context. The symptom was usually a
cost spike (the agent reading more than it needed) or a
quality regression (the agent producing work shaped by
context it shouldn't have had).

T-ab8 (per-milestone memory branching) had closed the bleed
at the episodic-memory layer. T-ab9 (milestone seed filter)
had closed it at the seed-pool layer. T-ab48 (write-time
validator) had closed it at the story-emission layer. But
the bleed kept appearing in new forms:

- **T-ab34** — scope existing-artifacts framing blocks to
  active milestone (framing prose was including off-scope
  context).
- **T-ab35** — tool-level milestone scoping for read_file
  (agents were using tools to read off-scope files even
  when the substrate's seed pool wouldn't have surfaced
  them).
- **T-ab45** — scope-lock framing on scoping + composition
  directives (the framing for these meetings still leaked
  off-scope artifacts despite seed-pool filtering).
- **T-ab46** — filter list_files to active milestone in
  scoping/composition (agents using list_files saw off-scope
  files even with read_file scoped).

Each fix patched a specific surface. None of them got at the
underlying invariant: **every read of milestone-scoped state
should be filtered to the active milestone.** The fixes were
playing whack-a-mole with the surfaces while leaving the
invariant unenforced at the substrate level.

### T-ab51 — the keystone

Finally, T-ab51 shipped as **the milestone-scope filter at
the seed-resolution layer**. The fix recognized that all the
prior patches were treating individual symptoms; the real
bug was that the seed-pool resolver, when asked for
artifacts of a given kind, returned EVERYTHING of that kind
on disk and let downstream code filter. By moving the
milestone filter to the seed-resolver itself, every
downstream consumer inherited the filter for free.

T-ab51 closed the bleed across requirement + story + feature
axes simultaneously. Audit revealed that some downstream
surfaces had been filtering requirements correctly but not
stories, others stories but not features. The keystone fix
unified all three under one invariant.

The architectural insight: **invariants belong at the read
point, not at every consumer.** Fixing a bleed at every
downstream surface is fragile because new surfaces keep
appearing; fixing it at the source eliminates the class of
bug entirely. Same pattern as input validation in web
security: validate at the boundary, not in every handler.

### T-ab52 — write isolation needed read-side teeth

A subtler architectural finding emerged from the obol pilot
post-mortem. T-ab8's per-milestone memory branching
isolated WRITES — a milestone's deliberation would write
into its own memory branch. But it did not isolate READS.
The `compose_context` helper that retrieved relevant
memory for an agent's deliberation bypassed the
inheritance_chain that branches were supposed to provide,
reading from all branches indiscriminately.

The symptom: even with per-milestone branching, an agent
could still see episodic memory from adjacent milestones
because `compose_context` queried the full memory store,
not the active branch.

T-ab52 fixed `compose_context` to honor the inheritance
chain. Write isolation finally had read-side teeth.

The architectural insight, paper-grade: **memory branches
that isolate writes but not reads provide the illusion of
isolation without the substance.** The whole purpose of
branching is to bound what the agent sees during
deliberation; if reads escape the branch, branching
becomes accounting overhead with no behavioral effect.
The fix required auditing every memory-read site for branch
honoring, not just the obvious ones.

### T-ab53 — implicit milestone derivation for implement runs

The implement workflow (tdd-implement) needed to know the
active milestone to scope correctly. Earlier code had
required the active milestone to be set explicitly by the
caller. T-ab53 added implicit derivation: if there are
queued + in-progress features all in the same milestone,
that's the active milestone. The substrate could now infer
scope from the work itself, eliminating a class of
"forgot to set active milestone" operator errors.

### The Phase 3 substrate after the fixes

By the end of Phase 3, the cross-milestone bleed pattern
was closed at the architectural level — every read of
milestone-scoped state inherited the filter from the
seed-resolver, the memory branches had read-side teeth, and
the implement workflow derived its scope from the work
itself.

Phase 3 also surfaced what the next pilot would need to
test: whether the substrate's per-milestone cost trajectory
("foundation-once, capability-cheap") would actually
materialize when cross-milestone bleed was structurally
impossible.

mvp-demo-redux was that pilot.

---

## §6.6 — Phase 4: Cost trajectory hardening (T-ab54 — T-ab64)

mvp-demo-redux re-ran mvp's notebook spec on the
post-T-ab53 substrate. **$30.58 vs the original $83.78**
— a 63% cost reduction on identical scope, same model,
same per-MTok pricing
([analysis 046](https://github.com/KohlJary/wonderland-ai/blob/main/analyses/046-mvp-redux-cost-receipt.md)).
The per-milestone trajectory showed the predicted shape
for the first time: M1 foundation $15.59, M2 capability
$10.91, **M3 capability $3.72** — capability work building
on solid foundation, decreasing monotonically as the
foundation amortized.

This was the substrate's first cost-trajectory receipt.
The Phase-3 fixes were validated. The next set of fixes
hardened against the remaining gaps cost analysis surfaced.

### T-ab54 — M8 review roster narrowed to Caterpillar-only

obol-260522 telemetry showed Tweedles spending 2.2×
Caterpillar's cost in M8 review meetings at 80% pass rate —
pure window-opening overhead. The Tweedles' contributions
to review were mostly procedural acknowledgments; the
load-bearing review work was Caterpillar's.

T-ab54 narrowed the M8 roster to Caterpillar solo. Tweedles
were removed from `team_groupings`. The pass-rate stayed
high (Caterpillar alone caught what Caterpillar-plus-Tweedles
caught), and the per-M8 cost dropped sharply.

In the redux pilot, M8 review consumed ~11% of total cost
instead of the ~30%+ it had consumed pre-fix. Same review
quality, third the spend.

### T-ab57 — tool-result cap

Tool results (from `read_file`, `list_files`, `verify_imports`,
etc.) were being returned to agents at full length. Some
returns were many KB. Each return participated in the agent's
deliberation context and got cached, paid for, and replayed
on every subsequent tool-use round-trip in the same
deliberation.

Cost analysis showed that 52% of total tool-result bytes
across all tool-using agents were lying in deliberation
context past the point of usefulness — Mad Hatter's M6 work
was the biggest single contributor (he reads test scenarios
in detail then doesn't need the full text again).

T-ab57 capped tool results in the deliberation loop at 5K
characters. The first round-trip got the full result; subsequent
rounds got the cap. Aggregate bytes saved across all
deliberations: 52%. Quality unchanged.

The architectural insight: **deliberation context bloat
compounds across rounds because each round caches the
prior round's full context.** The cap exploits the
observation that agents rarely re-read the full text of a
prior tool result; they want enough context to remember
what they saw, not the verbatim text. A cap that preserves
the head of the result keeps the actionable detail bounded.

### T-ab60 — source-line context in npm build failures

When npm build failed, the agent received the raw error
text. TypeScript errors typically point at a file:line and
say "Type 'X' is not assignable to type 'Y'" — actionable,
but without the surrounding source the agent has to read the
file separately to understand the context. The result was
multi-cycle convergence: agent reads error, reads file,
proposes fix, fix breaks something else, re-runs build,
reads new error, reads file again, etc.

T-ab60 extracted the failing line ± 3 surrounding lines from
each error location and embedded them in the finding. The
agent now sees both the error and the context together. In
the LDR pilot's first build failure, convergence dropped
from the typical 5-cycle dance to a single pass: the agent
read the contextualized error and produced the fix in one
round.

The architectural insight: **structural context at the
point of failure compresses convergence cycles.** It's the
same insight T-ab30 (per-test traceback in verify findings)
applied to a different verification surface. Both fixes
encode the principle: when the substrate surfaces a failure,
include enough context that the agent can act on it without
a separate read round.

### T-ab62 — requirement citations in phantom-citation filter

The phantom-citation filter (a substrate invariant: every
artifact's `sources` must resolve to real upstream artifacts
on disk) was dropping the LDR pilot's M2 feature. The
feature's sources cited the milestone's `consumes_requirements`
slugs — legitimate citations of foundation-milestone work
— but the filter only validated against story + milestone
slugs, not requirement slugs.

T-ab62 widened the filter to accept requirement citations
as valid feature sources. The invariant was real (drop
drift-corrupted citations), but its scope was
under-permissive (it rejected legitimate foundation-feature
citations). Widening the valid set preserved the
drift-detection while unblocking the legitimate flow.

The architectural insight, paper-grade: **substrate
invariants need to evolve as the substrate's typed-state
relationships evolve.** When foundation milestones produced
features that descended directly from requirements
(skipping the intermediate story layer), the citation chain
became `feature.sources → requirement` instead of
`feature.sources → story`. The filter's set of valid source
kinds had to expand to keep up. Diagnostic took longer than
the fix: ~2 hours to trace the drop, ~2 lines of substantive
code change to fix it.

### T-ab64 — end-to-end verification gates

The LDR pilot exposed a class of failure the prior
verification stack couldn't catch: **hollow features**.
Features marked `verified` lifecycle state whose UI surface
was placeholder text, whose components were orphaned
(imported nowhere), whose backend endpoints were missing
despite the frontend calling them, whose mocked data was
never replaced with real implementation. The existing M9
gates (pytest_collects, pytest_passes, npm_build) all
passed cleanly because per-layer checks compose without
catching cross-layer hollowness: pytest passed because only
the skeleton test existed; npm build was clean because
orphan TypeScript components still compile; Caterpillar's
review reads code but doesn't run it.

T-ab64 added four end-to-end composition checks to M9:

- **frontend_imports_reachable** — every .tsx component
  must be reachable from the entry point via the import
  graph. Catches orphan components.
- **api_call_resolves_to_route** — every `/api/...` URL
  string in the frontend must resolve to a registered
  FastAPI route. Catches missing backend endpoints.
- **no_placeholder_on_render_path** — no TODO/FIXME/
  placeholder markers in files reachable from the frontend
  entry. Catches placeholder text shipped as user-facing
  output.
- **no_duplicate_modules** — no two Python modules export
  the same public API surface. Catches parallel-write
  collisions (two agents wrote the same utility
  independently).

All four are skeleton-gated: backend-only / library / CLI
skeletons skip the frontend checks; pure-frontend skeletons
skip the backend checks. Same silent-degradation pattern
that pytest_collects and npm_build already use.

The architectural insight, paper-grade: **per-layer
verification doesn't compose into end-to-end verification.**
The substrate had per-layer gates (tests, builds, reviews)
but no gates that asked "does the feature actually deliver
end-to-end?" The hollow-verify gap was structurally
predictable from the framing — when a state transition's
admission criteria are defined as a conjunction of local
checks, the transition can fire on hollow data if no global
invariant binds the locals together. T-ab64 added the
binding invariants.

Validated against the LDR pilot's directory: catches all
four substantive findings the operator noticed manually
(NewsCard orphan, /api/news unregistered, /api/messages
skeleton ghost, auth/security duplication). Validated
against the redux pilot: catches one known-harmless finding
(/api/messages skeleton ghost from api.ts already
documented in analysis 046).

### The Phase 4 substrate after the fixes

By the end of Phase 4, the substrate had:

- A cost trajectory across two pilots that demonstrated
  the constraint→quality+cost coupling at scale.
- M8 review compressed to its load-bearing voice (Caterpillar
  solo) without sacrificing pass-rate.
- Tool-result deliberation context bounded by structural cap.
- Verify findings carrying enough context to compress
  convergence cycles.
- Phantom-citation invariants expanded to admit legitimate
  foundation-milestone citation chains.
- End-to-end composition gates catching hollow-feature
  shipments that per-layer gates missed.

The pending LDR re-run will test whether T-ab64 closed the
hollow-verify gap operationally. The substrate's invariant
stack is at its strongest to date.

---

## §6.7 — The pattern across all four phases

Stepping back from the individual fixes, the substrate
evolution arc reveals several patterns worth naming.

### Every fix is structural

Across ~60 substrate fixes (T-i + T-m + T-v + T-g + T-ab1
through T-ab64), almost none modify agent prompts or
constitutions. The fixes are at the substrate level: typed
field additions, lifecycle invariant changes, seed-pool
filter rules, memory branch enforcement, verification check
additions, tool access guards. The agents themselves are
remarkably stable across the evolution — the constitutions
shipped in v0.4 are largely the constitutions running in
v0.10.2.

This is what Corollary 6 predicts: substrate constraints
let identity carry more of the discipline from inside, so
the work of improving the system happens at the substrate
layer, not the agent layer. The agents get cheaper to
coordinate as the substrate's invariants multiply, not
because the agents got smarter, but because the substrate
got better at refusing to admit transitions the agents
would otherwise produce.

### Each fix encodes a missing invariant

The substrate fixes are not arbitrary improvements; each one
encodes a structural invariant the substrate should have
been enforcing all along but wasn't. The invariants
discovered:

- Citations must resolve to real upstream artifacts on disk
  (phantom-citation filter, T-ab62 widening)
- Active milestone scope must filter every read site, not
  just specific consumers (T-ab51)
- Memory branches must isolate reads, not just writes
  (T-ab52)
- Feature emissions must declare an explicit milestone tag
  (T-ab48)
- Substrate paths must be perimeter-enforced — agents can't
  write to typed-state directories out-of-band (T-ab12)
- Frontend API calls must resolve to backend routes (T-ab64)
- Frontend components must be reachable from the entry point
  (T-ab64)
- Two modules can't export the same public API (T-ab64)
- Cycles must converge — verify-spawned tickets must be
  fresh per cycle, not stale (T-ab28)
- Tool-result context must be bounded structurally, not
  by agent self-restraint (T-ab57)

Each invariant is, in retrospect, obvious — the substrate
should always have had it. The iteration cycle's job is to
discover these invariants empirically, surface them as
substrate-level fixes, and accumulate the stack.

### The cost trajectory is the invariant stack's signature

The two-pilot cost trajectory ($83.78 → $30.58, 63%
reduction on identical scope) is not produced by any single
fix. It's the aggregate signature of the invariant stack.
Approximate per-fix attribution against the $53.20 absolute
gap, derived from observed per-fix savings + cross-pilot
cost-pattern comparison:

| Fix or fix cluster | Approximate contribution | Mechanism |
|---|---|---|
| **T-ab51** (keystone milestone-scope filter at seed-resolution layer) | ~30-40% of the gap | Closed cross-milestone bleed across requirement + story + feature axes simultaneously. Eliminated the rework cycles that drove obol-260522's cost-rise pattern. Observed by absence: redux's design-side cost per milestone is 60-70% lower than obol-260522's, with the substrate-version delta being primarily T-ab51's invariant. |
| **T-ab54** (M8 roster narrowed to Caterpillar-only) | ~15-20% of the gap | Tweedles removed from review meeting; ~$8/M8 cycle direct savings on obol-260522 telemetry. M8 spend dropped from ~30% of total in mvp pilots to ~11% in redux, with no review-quality regression. |
| **T-ab8 + T-ab52** (per-milestone memory branching + read-side teeth) | ~10-15% of the gap | T-ab8 was already shipping in mvp's substrate (T-a2 era); T-ab52 closed the read-side leak that made T-ab8's write isolation incomplete. The combined effect eliminates the memory-bleed wedges that drove mvp-demo's M4 to ~22 rotations on stale requirements. |
| **T-ab57** (tool-result cap in deliberation loops) | ~10-15% of the gap | 52% of total tool-result bytes saved across all tool-using agents. Bytes don't map 1:1 to cost (caching dynamics), but the bytes saved correlate strongly with cache-replay overhead on subsequent rotation rounds. |
| **T-ab16 — T-ab19** (iteration efficiency filters) | ~5-10% of the gap | Empty-iteration skipping (`iterate_only_with_tickets`, implicit milestone scope, cross-milestone emission rejection, no-in-scope-tickets M4 skip). Each opens fewer priority windows on items where deliberation produces no signal. |
| **T-ab30 + T-ab60** (per-test traceback + source-line context in verify findings) | ~5% of the gap | Compressed npm-build convergence from typical 5-cycle dance to 1-pass in the LDR pilot. Smaller absolute contribution because the failure-path is rarer, but the per-cycle savings on the build-failure trigger are real. |
| Residual (other Phase 2-4 fixes, cache dynamics, secondary effects) | ~5-15% | Smaller fixes (T-ab43 disk reconciliation, T-ab44 meeting ID, T-ab23 swallowed-crash catching, T-ab24 memory-recall budgeting, T-ab27 nudge filtering, T-ab28 verify ticket synthesis, others) each contribute modestly; aggregate is real but not individually large. |

The attribution is **approximate by necessity** — the fixes
compound non-additively, exact per-fix isolation would
require A/B re-running each fix's substrate version against
each other in matched-on-task comparisons, and even that
wouldn't disentangle interaction effects between fixes that
close related classes of waste. The table reports best-
available per-fix observations + qualitative reasoning about
mechanism rather than statistically-clean attribution. It is
presented to give a reader a sense of which fixes carry
which fraction of the load; it is not presented as
defensible decomposition for purposes of single-fix
optimization claims.

The fixes compound because each one closes a class of waste
the prior fixes didn't catch. The architectural commitment that makes the
compounding work: **substrate fixes encode missing
invariants, so they don't conflict with prior fixes; they
extend the invariant stack.**

A fix that improved one agent's prompt might trade off
against another agent's behavior. A fix that adds a
structural invariant doesn't trade off — it narrows the
grammar of legitimate emissions, which downstream agents
benefit from regardless.

### The state-machine framing predicts where gaps appear

A second-order pattern: the gaps the iteration cycle
discovered are exactly the gaps the state-machine framing
predicts. When the substrate's typed-state transitions are
defined as conjunctions of local checks, transitions can
fire on hollow data if no global invariant binds the locals
together. The hollow-verify gap (T-ab64) is the canonical
example: pytest passes + npm builds + Caterpillar reviews
+ operator approves are all local checks, none of which
asks "do these compose into a working end-to-end
deliverable?"

The same shape applies to cross-milestone bleed (each
read site checked scope locally, but no invariant bound
them at the resolver), to phantom citations (each
artifact's sources were locally well-formed, but no
invariant bound them to disk reality), to memory bleed
(write isolation was a local property, but reads escaped
it).

The state-machine framing isn't just descriptive — it
predicts where the next substrate gap will be. **Wherever
a transition's admission criteria is a conjunction of
local checks without a binding global invariant, the
substrate is one pilot away from discovering that the
transition can fire on hollow data.** The methodological
upshot: future substrate work should pre-emptively look for
transitions whose admission criteria lack global binding
invariants, and add the binding before the next pilot
exposes the gap.

### Operator-in-loop as falsification mechanism

The iteration cycle depends on the operator running pilots
in earnest and noticing gaps that automated checks pass
over. The hollow-verify gap was operator-noticed (Theseus
review surfaced it from a fine-tooth-comb code review the
operator ran post-pilot). The cross-milestone bleed was
operator-noticed (cost spikes on obol-260522 didn't match
expected per-milestone trajectory). The Caterpillar
silence-bias was operator-noticed (M8 review producing no
artifact despite reading code).

This is what makes the substrate's iteration cycle
**science** rather than engineering polish. Each substrate
fix is a falsified prediction: the prior substrate said
"this transition is admissible"; the operator says "no,
the transition fired on hollow data, here's the
counter-example"; the fix encodes the missing invariant.
Without the operator's adversarial gaze, the substrate's
gaps remain hidden behind passing tests. With them, the
substrate's invariant stack grows monotonically.

The methodological commitment Wonderland makes is that
the operator IS part of the substrate's design loop, not
just its user. The pilots are the experimental harness;
operator-noticed gaps are the experimental results; the
substrate fixes are the theoretical refinements. The
two-pilot cost trajectory is the empirical signature of
this loop functioning correctly.

---

## §6.8 — What comes next

The substrate's iteration cycle is open-ended. Several
classes of work are queued or in flight:

### Template-similarity milestone consolidation (T-ab63)

When the planner produces multiple capability milestones
that share the same architectural template (consume
foundation X → fetch external data → render on surface Y),
they should consolidate into one milestone with N features.
LDR's M3/M4/M5 (time, weather, news cards) were the
canonical case — three separate milestones with identical
shape. T-ab63 will teach the planner to detect the
template-similarity pattern and consolidate.

Deferred until parallel coordination ships (see below);
consolidation maximizes the surface area parallel
coordination applies to, so they pair multiplicatively.

### Parallel coordination

The substrate currently runs serially — one milestone at a
time, one feature at a time within a milestone, one ticket
at a time within a feature. The substrate's typed-state
machinery already supports parallel orchestration in
principle: per-milestone memory branching isolates
concurrent milestones; feature-level lifecycle states are
orthogonal across features; `gates_on_dependencies` in M7
already supports per-ticket dependency gating. What's
missing is a coordinator that decides "these N features
can run M7 in parallel" based on the dependency graph, and
the orchestration to actually fan them out.

Parallel coordination is the wall-clock-time lever. Cost
optimizations from prior phases got the per-pilot spend
down; parallel coordination gets the per-pilot time down.
Together with template consolidation, this is what closes
the gap to systems like Devin that compete on wall-clock
rather than per-task quality.

### The LDR re-run

The LDR pilot is being re-run on the post-T-ab64 substrate.
Outcomes: either the four end-to-end gates catch the
hollow-feature class operationally (third receipt for the
cost trajectory + validation that T-ab64 closed the gap),
or the re-run surfaces a new substrate gap T-ab64 doesn't
cover (next substrate fix, next iteration cycle).

Either outcome is paper-grade. Receipts and substrate
findings both extend the invariant stack.

### Existing-codebase / change-request feature surface

The substrate currently bootstraps from a directive + a
skeleton. It doesn't yet support "here's an existing
codebase, implement this change request." Adding this
surface would let the substrate handle the most common
real-world software work shape: iterating on existing
software, not green-field MVPs.

The architectural work: ingesting an existing codebase into
the typed-state substrate (every existing file becomes
artifact-attributed; every existing dependency becomes a
contract), then running the design-implement loop against
the augmented state.

### Multi-operator concurrency

Single-operator pilots dominate the substrate's evolution
to date. The substrate is theoretically multi-operator-
ready (typed state is the canonical source; agents don't
care which operator is in the loop), but the operator-in-
loop falsification mechanism currently assumes one operator
per pilot. Multi-operator concurrency would test whether
the falsification mechanism scales — does two operators
running pilots in parallel produce twice the substrate
findings, or does the substrate's invariants converge to
the union of both operators' observation power?

### Other model families

The substrate currently targets Claude Haiku 4.5.
Generalization to other small models (open-weight or
otherwise) is future work that would test whether the
substrate-amplifies-identity claim is Haiku-specific or
applies to small models generally.

---

## §6.9 — Closing frame

The substrate's evolution is the methodology. Each phase
shipped a load-bearing layer of structural invariants the
prior phase lacked. The cost trajectory developed in the
Phase 4 section above is not a one-shot win; it's the
aggregate signature of an invariant stack that took ~60
substrate fixes to accumulate. The next pilot's cost will
be determined by whatever invariants the current stack
still lacks; the iteration cycle will discover them.

The architectural commitment that makes this work — that
state is primary, agents are transition functions over
typed durable artifacts, invariants belong at the
substrate level rather than the agent level — is what
allows the fixes to compound rather than trade off. A
multi-agent system that improved through agent prompt
tweaks would see prompt edits collide; an agent's
behavior tuned for one situation would degrade in
another. Substrate invariants don't collide because they
narrow grammar; the agent is still free within the
narrowed grammar, but the substrate refuses to admit
emissions outside it.

**This is the chapter's load-bearing claim: building a
multi-agent SDLC system that produces working code at
low cost on small models is not a matter of finding the
right prompts or the right model. It is a matter of
accumulating the right structural invariants over typed
state, and the discovery process for those invariants is
the iteration cycle this chapter documents.**

Identity engineering is the discipline. The substrate
invariant stack is identity engineering's empirical
backbone. The iteration cycle is identity engineering's
methodology. Wonderland is one instance; the paper is
the case for the discipline being worth pursuing beyond
this instance; this chapter is the receipt for the
discipline functioning.

---

