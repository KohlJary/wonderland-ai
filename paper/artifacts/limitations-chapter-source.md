# §8 — Limitations

## §8.1 — The publishing-snapshot premise

Before naming any specific limitation, the chapter has to
make a methodological commitment that frames everything
below: **this chapter documents the limitations of the
Wonderland substrate at the publication-snapshot version,
not in perpetuity.** The iteration cycle documented in the
substrate-evolution chapter (§6)
is open-ended; every limitation in this chapter is either:

1. **Already addressed** in a substrate fix that shipped
   between the gap being observed and the paper being
   written (named here as historical context — the
   limitation existed, it was named, it was fixed; the
   chapter cites it to show the iteration cycle working).
2. **Addressed with the fix shipped, validation pending**
   in the next pilot (LDR re-run for the T-ab64 fix is
   the canonical example).
3. **Open with a filed roadmap fix and a known timing**
   (parallel coordination, template-similarity
   consolidation, multi-operator concurrency — each has a
   filed task and a known sequencing).
4. **Open with no filed fix because the right shape
   isn't yet known** (the P7 generic-baseline eval is the
   clearest example — we know we should compare, we don't
   yet have the right harness design).

The chapter is written this way because publication is a
snapshot, not an end. Every paper that documents an
ongoing research artifact has to draw a publication line
through a moving target; the right discipline is to draw
the line where the substrate is most receipt-worthy, name
what's open as of that line, and continue the iteration
cycle past the line. The alternative — waiting until
nothing is open — is structurally impossible for a
research artifact whose evolution surfaces new gaps with
every pilot. **The limitations below are not defeats; they
are the visible edge of an iteration cycle that has, to
date, closed every prior class of limitation it has
surfaced.**

This framing is load-bearing for the chapter and the
paper. A reader who reads "limitations" as
"unsolved-and-likely-unsolvable" misreads what the
chapter is doing. The reader who reads "limitations as
publishing-snapshot of an iteration cycle, each with
either a filed fix or a known reason no fix exists yet"
reads the chapter at the right epistemic register.

---

## §8.2 — What counts as a limitation here

This chapter distinguishes four classes of limitation, each
with a different epistemic shape:

| Class | Shape | Examples |
|---|---|---|
| **Substrate gap** | Known failure mode with a filed fix (often in roadmap). | b3f440c8 cluster; Caterpillar's static blindspot. |
| **Scope-bounded validation** | Claim holds in the spec'd use case but would fail outside it. | B1 + C2 from code-quality artifact (latent at v1, acute at v2). |
| **Sample-size limit** | N is too small to support a stronger claim than "observation with mechanism." | N=2 pilots; one directive class; one model class. |
| **Missing rigor** | Comparison or eval that would strengthen the claim hasn't been run. | P7 generic-baseline eval; single-shot Haiku/Sonnet comparison baselines. |

---

## §8.3 — Substrate gaps

### The "prior-milestone-awareness" cluster — closed

The mvp Tier 2 pilot surfaced four substrate gaps
(b3f440c8 sibling-feature visibility, 4a2597a4 cross-feature
consolidation, 81af78f8 two-tier feature presentation,
e7d226b8 coverage check aware of shipped implementations)
that shared a single theme: the substrate had limited
awareness of prior-milestone shipped work at different
layers. The cluster is documented in detail in §6 (substrate
evolution); it has been closed by the keystone milestone-scope
filter (T-ab51) plus iteration filters T-ab17 + T-ab18 + the
scope-framing fixes T-ab34 + T-ab46 and iteration-pruning
T-ab41. Tier 2 autonomy at the post-T-ab51 substrate no
longer requires the operator's duplicate-skipping discipline
that mvp's pilot needed. Cited here as the canonical example
of an open limitations cluster closing through iteration; the
still-open items follow.

### Hollow-verify gap (LDR exposure, T-ab64 closure, validation pending)

the LDR pilot at substrate 0.10.2 + T-ab62 exposed a class
of failure the M9 build_check stack couldn't catch — features
that ship in `verified` lifecycle state with hollow
deliverables (orphan UI components calling non-existent
backend endpoints, placeholder dashboard text, hardcoded
mocked data never replaced, parallel-write duplicate modules).
Per-layer checks (pytest, npm build, Caterpillar review,
operator gate) all passed cleanly because each check is local
— none asks "do these compose into a working end-to-end
deliverable?"

The substrate exposed-and-addressed cycle:

- **Exposure**: LDR pilot completed at $19.44 with six
  features marked `verified`. Operator-commissioned Theseus
  review surfaced the hollow-feature pattern across
  multiple features. Documented as a memory observation +
  the substrate-gap entry above.
- **Diagnosis**: per-layer M9 checks compose without
  catching cross-layer hollowness. The state-machine
  framing predicts this — when a lifecycle transition's
  admission criteria is a conjunction of local checks
  without a binding global invariant, the transition can
  fire on hollow data.
- **Closure**: T-ab64 shipped four new M9 end-to-end
  composition checks (frontend_imports_reachable,
  api_call_resolves_to_route,
  no_placeholder_on_render_path, no_duplicate_modules) all
  skeleton-gated to skip silently when project shape
  doesn't match. Validated against the LDR pilot directory:
  catches all four substantive Theseus findings.
- **Validation pending**: LDR re-run on the post-T-ab64
  substrate will produce either a clean third receipt
  (validating T-ab64 closed the gap operationally) or
  surface a residual gap T-ab64 doesn't catch (next
  iteration cycle's input). Either outcome is paper-grade.

The original LDR $19.44 is documented honestly: it is **not
cited as a working-app receipt** because the deliverable
was hollow. It is cited as the cost of the pilot that
exposed the hollow-verify gap, which is itself a valuable
research artifact — the gap was found at $19.44 of pilot
spend, which is structurally cheaper than the gap remaining
hidden behind passing tests until the substrate hits a
larger project where it would be more expensive to surface.

This is the canonical demonstration of the iteration-cycle
discipline working cheaply: a substrate gap surfaced in a
$20 pilot, addressed in a ~200-line substrate fix, validation
pending in the next pilot. The publishing-snapshot premise
above is what makes this a defensible "limitation" — the
fix shipped, validation is in flight, and the chapter
documents it openly rather than pretending the original
pilot was clean.

### Adjacent: stronger contextual signal per phase

Three roadmap items share a related theme — *"agents need
stronger contextual signal per phase"* — but at a different
layer than the cluster above:

- **79ef174a — Persona-anchoring in milestone-plan.** The
  tdd-design entry meeting prepends a milestone-framing
  block that names the active persona; milestone-plan has no
  equivalent. Alice gets confused about persona during
  milestone-plan. Surfaced in mvp; small directive
  edit, substrate-side helper.

- **Auto-directive synthesis** (shipped mid-pilot,
  124b5858). Was a Tier 2 violation made explicit. When
  `run_workflow` fires with empty directive AND an active
  milestone scope, synthesize one from milestone fields.
  Caterpillar got M2 design right (search story) but Alice
  drifted into M1-flavored stories (capture flow) because
  the per-run signal of "you are designing M2 specifically"
  wasn't strong enough. The fix shipped + held in M3 design.

- **837b5bbb — Feature sequencing (Feature.depends_on).**
  Operator's observation during mvp: *"putting features
  in an order would as a byproduct result in more tightly
  designed features."* Currently features are a bag; explicit
  dependency would force Rabbit during M2 to think about
  what each feature delivers + what enables it. Same shape
  as snapshot semantics + milestone scoping: constraints
  improve quality. Partially resolves b3f440c8.

These items aren't substrate gaps in the cluster sense —
they're targeted single-point additions. But they share the
underlying pattern that *the agents need more structure per
phase than the current substrate provides*.

### M1-overshoot pattern (milestone boundaries are advisory)

in mvp-demo, M1's implementation pass shipped working
backend AND frontend, overshooting 3 milestones deep. M2 +
M3 design then wedged because no actionable delta remained.

The architectural observation: **once Tweedles start, they
build the whole app.** Implementation budget doesn't respect
milestone scope at the Tweedle level. They're optimizing for
"make this work as a system," not "stop at milestone N's
boundary." This is the architectural choice that produces
the overshoot.

Framing options for the paper:
- **Positive:** Wonderland over-delivers per implementation
  pass.
- **Negative:** Milestone boundaries are advisory, not
  enforced.

Both framings are accurate. The chapter should be honest
about both. The forward implication: milestone-plan should
detect overlap risk at planning time (forward-realization
check between milestones); currently the planning pass
doesn't compute this. Not yet filed as a discrete roadmap
item; lives as a known pattern.

---

## §8.4 — Known model-class limits

### Caterpillar's static blindspot

M8's review reliably misses single-file static-time bugs —
Pydantic field/type shadows, unresolved forwards, decorator
order traps. Class of bug that "would not even import"
ships through M8 untouched.

The root cause: M8 prioritizes cross-ticket coherence FIRST
(per analysis 040), the failure mode no single-file review
can catch. That prioritization explicitly trades against
per-file static-time correctness. Caterpillar reads code;
she doesn't load it.

**The fix exists** and shipped — `verify_imports` tool
exposed to Caterpillar (T-v5) gives a mechanical check for
the most common class. M9's `pytest_collects` build-check
catches the rest. So this is a "known limit + known fix"
rather than an open gap; the chapter should mention it as
evidence of the categorization-through-failure discipline
(name the class, ship the right-sized fix, move on).

### Cross-endpoint behavioral integration invisible to M8

Per the [code-quality analysis §6.2](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/code-quality-mvp.md#62-c2-cross-endpoint-serialization-mismatch--failure-mode-of-m8-static-review):
the C2 finding (revision_id serialization mismatch — same
note produces different revision_ids depending on which
endpoint surfaced it) is the canonical M8-blindspot pattern
at a different layer than the static blindspot above.

Both functions read correctly in isolation. The bug only
manifests when a client uses a revision_id from one
endpoint as the If-Match for another. M8 reads files for
coherence, not behavioral integration across endpoints.
M9's `pytest_passes` would catch it IF an integration test
existed; the test gap (no PUT/collision tests, no
audit-log tests) and the implementation gap reinforce each
other.

**The right-sized fix is cross-endpoint scenario coverage as
a first-class Hatter generation prompt during M6** — Hatter
generated scenarios for search-escaping but not for
revision_id round-tripping. Filed as future-work, not yet
implemented.

Scope honesty: this finding is latent in mvp's spec'd
use case (single-user, no concurrent writers). It would
become acute if the spec grew to multi-user. The substrate
built the optimistic-locking infrastructure correctly enough
for the scope; the bug is evidence about substrate reach,
not about whether the shipped artifact works.

### Frontend test coverage gap

Per the code-quality artifact reviewer findings: `vitest`
is installed in `demo/mvp/frontend/package.json` but zero
frontend tests exist. The Tweedles' M7 directive doesn't
require Hatter scenarios to be translated into runnable
frontend tests; M9's `npm_build` verifies compile + bundle,
not behavior.

This is the single biggest test-coverage gap in the shipped
artifact, and **it's exactly where the substrate has no
enforcement loop**. Backend tests get written because M9's
`pytest_passes` build-check exists; frontend tests don't
get written because there's no parallel.

The right-sized fix: M9 gains an `npm_test` build-check
parallel to `pytest_passes` / `npm_build`; M7's directive
gains an explicit requirement that the Hatter scenarios for
this ticket exist as runnable tests in the appropriate test
directory. Filed as future work.

---

## §8.5 — Sample-size limits

The chapter should be explicit that current evidence has
sample-size limits that bound what claims can be made.

### N=3 working-app pilots + 1 stress-test pilot

Wonderland has run **three end-to-end pilots that produced
working-app artifacts** and one stress-test pilot that
exposed a substrate gap:

- **mvp** (notebook spec, substrate 0.8.0, $83.78)
  — first Tier 2 completion. Three milestones designed,
  implemented, verified.
- **obol-260522-1** (CRM project, substrate 0.9.0+early
  0.10.0, $92.64) — second Tier 2 pilot, larger scope.
  Surfaced the cross-milestone bleed pattern that drove
  Phase-3 substrate work (T-ab51).
- **mvp-demo-redux** (notebook spec, substrate 0.10.1,
  $30.58) — re-ran mvp's directive on the
  post-T-ab51-T-ab57 substrate. Genuine working-app
  receipt at 36% of the original spend.
- **LDR** (long-distance dashboard, substrate 0.10.2 +
  T-ab62, $19.44) — exposed the hollow-verify gap.
  Pilot completed through to `verified` lifecycle states
  but the deliverables were hollow; T-ab64 then closed
  the gap; re-run pending for working-app receipt status.

Earlier work (P1-P19, including mvp-demo) tested substrate
primitives but didn't reach Tier 2 end-to-end completion.

What N=3 + stress-test means for the claims:

- **The mechanism is predictive even at low N.** Each
  pillar in the evidence chapter is framed as
  "observation + mechanism" — the mechanism makes the
  pillar falsifiable in future pilots even at current
  sample size. The two-pilot cost trajectory ($83.78 →
  $30.58 on identical scope) is mechanism-grounded; if
  future pilots break the trajectory, the mechanism needs
  revisiting.
- **No statistical claims.** The chapter does not frame
  any claim as "across N pilots, X% of the time…" — N=3
  doesn't support that shape; the substrate-version
  variance across the pilots wouldn't support it even at
  larger N.
- **The cross-pilot pattern is identifiable.** Each pilot
  is an independent realization on a different substrate
  version against a different (or in redux's case,
  intentionally-identical) directive. The pattern across
  pilots is mechanism-instantiation, not statistical
  regularity.
- **Future pilots strengthen specific claims.** Each pilot
  adds observations to each pillar; the mechanism gets
  stronger or gets refuted; the pillar's framing tightens.
  The LDR re-run is the next data point.

### One directive class (notebook-shaped)

Both mvp-demo and mvp used variants of the
"personal markdown notebook web app" directive. Cross-pilot
comparison is meaningful (same directive class on different
substrate versions) but the substrate's properties haven't
been tested on:

- Backend-heavy projects (CLI tools, service daemons,
  background workers).
- TUI projects (the workflow already adapts via
  `runtime: tui` framing, but no pilot has shipped one).
- Mobile / desktop app projects.
- Domain-specific shapes (data pipelines, ML systems,
  scientific computing).

the workflow YAMLs are designed to be atomic and
composable; Dodo dynamically chaining workflows for
different work shapes (incident response, security audit,
hotfix) is the architectural direction. But the chaining
infrastructure isn't built yet; the pilots that would
validate cross-shape transferability haven't run.

### One model class (Haiku 4.5)

All claims are at `claude-haiku-4-5-20251001`. The
Haiku-as-thesis-statement framing
predicts identity-and-substrate amplification holds across
model classes, but only one model class has been tested at
pilot scale.

What's been observed qualitatively in development work
(mostly Sonnet-driven coding sessions, not Wonderland pilots):
the substrate primitives work the same way regardless of
model class. What hasn't been measured: whether quality-cost
coupling holds at Sonnet's higher per-token rate, or whether
Sonnet without the substrate matches Wonderland-on-Haiku
output quality (the P7 eval).

---

## §8.6 — Missing rigor

### Comparative experiments — gaps, with planned closures in future work

Two specific comparative gaps weaken the paper's rigor:
the **P7 generic-baseline-vs-identity-native eval** (would
test Corollary 1's "small models outperform via identity"
claim by running matched tasks against a generic-prompt
baseline at the same model class), and **comparison
baselines for code quality** (would test whether
Wonderland-on-Haiku's review-grade output exceeds what
Haiku-without-Wonderland or Sonnet-without-Wonderland
produce on the same directive).

Both are named here as gaps in the publishing-snapshot's
rigor and are developed as proposed experiments in §11
future-work, including the planned harness design, the
comparator-fairness concerns the methodology chapter names,
and the partial-progress single-shot Haiku/Sonnet baselines
that have been run against mvp's directive. The
chapter's claim is therefore bounded: Wonderland-on-Haiku
produces code an independent reviewer reads as competent
and above-average for an MVP at this scale; whether the
character framing produces this beyond what equivalent
operational rules alone would produce is the open question
the Appendix C comparator and a future P7 eval would test.

### Untested hypothesis: Haiku as architecturally optimal

the operator's qualitative read is that Opus might
*under-perform* Haiku on Wonderland — that the substrate's
constraints are calibrated for Haiku's capability shape and
larger models might over-reason against them. This is
**explicitly marked as untested**: *"I've observed that
qualitatively but I don't have, like, data to back me up on
it."*

The chapter should mention this as a hypothesis that
**future comparative pilots could test** rather than as a
claim. Including it in evidence would weaken the paper's
credibility; surfacing it as an open question in
limitations preserves intellectual honesty without
overclaiming.

---

## §8.7 — Tier 2 scope limits

The substrate has now run four Tier 2 pilots (mvp,
obol-260522-1, redux, LDR). Several limitations follow:

### Substrate maturity is per-directive-class

Tier 2 autonomy is claimed at the substrate version each
pilot ran on, on the directive class each pilot exercised.
Notebook-class directives have been validated (redux);
CRM-class directives have been validated (obol-260522-1);
dashboard-class directives produced the hollow deliverable
that exposed the verify gap (LDR; re-run pending on the
post-fix substrate). The chapter does not claim *"Wonderland
achieves Tier 2 autonomy"* as a general property; it claims
*"Wonderland achieves Tier 2 autonomy on directive class X at
substrate version Y."* Each new directive class shape tests
the substrate at a new boundary.

### Operator gate-approver discipline is qualitative

The Tier 2 distinction (gate-approver vs fixer) is named
operationally but isn't yet measured with rigor. Across
the four pilots, documented operator interventions include:

- mvp: 1 substantive scope clarification (full-text
  vs tag-only search), multiple duplicate-feature skips,
  ticket-level scope filtering on M3's megalith feature,
  1 mid-pilot substrate fix.
- obol-260522-1: cost-driver analysis during the pilot
  surfaced cross-milestone bleed; no substrate fix shipped
  mid-pilot but observation drove Phase-3 work.
- redux: operator-noticed verification of working app at
  pilot completion (curl-based CRUD + persistence checks);
  Theseus review post-pilot. Zero mid-pilot substrate
  fixes.
- LDR: operator-commissioned Theseus review post-pilot
  surfaced the hollow-verify gap; zero mid-pilot substrate
  fixes during the pilot itself (the end-to-end gate fix
  shipped between pilot completion and re-run setup).

The categorization "queue decisions ARE gate-approver work"
draws a line that's defensible but not formal. A future
methodology paper might propose a quantitative measure
(intervention frequency × intervention depth × substrate-state
impact); current paper describes the qualitative discipline
honestly without dressing it as metric.

### Mid-pilot substrate fix as Tier 2 violation

Across four pilots, only mvp required a mid-pilot
substrate fix (auto-directive synthesis). The subsequent
three pilots completed without mid-pilot violations,
strengthening the autonomy claim. The methodology chapter
argues mid-pilot fixes are honest documentation of
iterative substrate maturity when they happen; the limitations
chapter notes that **the post-mvp substrate has
matured to the point where mid-pilot violations are no
longer needed across three subsequent pilots**. This is
load-bearing for the autonomy claim — the substrate's Tier 2
readiness has gotten stronger across the pilot trajectory.

---

## §8.8 — Wall-clock time vs other systems

A class of limitation worth naming explicitly because it
distinguishes Wonderland's current scope from adjacent
systems: **Wonderland runs serially.** One milestone at a
time; one feature at a time within a milestone; one ticket
at a time within a feature. The substrate's per-pilot
cost has dropped to a regime where each pilot is affordable
(~$30 / pilot for the redux notebook), but the wall-clock
time hasn't compressed at the same rate. A pilot that
costs $30 still takes an hour to run.

This is what currently bounds Wonderland's competitiveness
on the dimension other autonomous coding systems (Devin,
agent-mode Cursor, Aider runs) optimize for. Devin-class
systems aim to compress wall-clock time, often at the cost
of per-task quality + structured artifacts. Wonderland
aims to preserve the quality + artifact stack while making
per-task cost affordable. The two trade against each
other along orthogonal axes; Wonderland has won on cost
+ quality while not yet competing on wall-clock.

The substrate's typed-state machinery already supports
parallel orchestration in principle: per-milestone memory
branching isolates concurrent milestones; feature-level
lifecycle states are orthogonal across features;
`gates_on_dependencies` in M7 already supports per-ticket
dependency gating. **What's missing is a coordinator that
decides "these N features can run M7 in parallel" based on
the dependency graph, and the orchestration to actually
fan them out.** Filed in future-work; deferred until
template-similarity milestone consolidation (T-ab63) lands
because the two pair multiplicatively (consolidation
maximizes parallelism's surface area).

This limitation is open at publication-snapshot. It is
**not unsolvable**; the architectural pieces are in place;
the orchestration work is scoped and pending. The chapter
documents it as the most prominent wall-clock-time gap to
date, paired with the substrate fix that closes it as the
publication-pending next iteration cycle.

### Engaging the Pareto-frontier critique

A hostile reading of this section would push: *"You've won
on cost + quality, but you haven't competed on the
dimension your nearest competitors optimize for. Isn't this
just a Pareto frontier point, not a Pareto improvement?"*

The honest answer is yes — Wonderland currently occupies a
specific Pareto-frontier corner (high quality + artifact
density, low cost, slow wall-clock) that the Devin /
Cursor-Agent / Aider quadrant doesn't. We are not claiming
Pareto dominance over the Devin-shaped quadrant; we are
claiming the existence of a different optimum on a
different dimension set. **This is a real and bounded claim:
the substrate occupies the cost+quality+artifact-density
corner of agent-system design space, with wall-clock as
the explicit traded-off axis.**

What makes the corner load-bearing rather than uninteresting:

- **Quality + artifact density compound across pilots.**
  The Devin quadrant's wall-clock advantage shrinks the
  more pilots an organization runs against the same
  codebase — every pilot's session log is opaque to the
  next pilot; every architectural decision has to be
  re-derived. Wonderland's typed durable artifacts (ADRs,
  contracts, lifecycle-tracked features, severity-tagged
  reviews) compound across pilots because they're
  designed as persistent state. The first pilot pays the
  artifact-creation cost; the tenth pilot benefits from
  the accumulated context. The Pareto comparison shifts
  across the artifact-density axis as pilot count grows.
- **Cost regime enables operator-in-loop falsification.**
  Per the methodology chapter (§5), the cost regime makes
  failure-exposing pilots affordable. Devin-quadrant
  systems' wall-clock advantage doesn't help if their cost
  regime makes pilot-N-of-twenty unaffordable.
- **The trade is closeable, not architectural.** Parallel
  coordination is the orchestration work that closes the
  wall-clock gap without sacrificing the cost + quality +
  artifact-density wins. The substrate's typed-state
  machinery already supports it; only the coordinator
  scheduling is missing. The current Pareto point is
  Wonderland-at-snapshot, not Wonderland-as-architecturally-
  bounded.

The hostile critique's strongest form ("you're trading off
the dimension that matters") rests on the assumption that
wall-clock IS the dimension that matters, which is true
for some use cases (rapid prototyping, hackathon-style
work, immediate-feedback iteration) and false for others
(long-running engineering projects, codebases that need
audit trails, work that benefits from accumulated context
across pilots). Wonderland's positioning targets the
latter; the Devin-class systems target the former; both
positions are defensible, and the wall-clock-time gap is
the cost of Wonderland's choice rather than evidence that
the choice was wrong.

