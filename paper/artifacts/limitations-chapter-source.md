# Limitations chapter source

> Source material for the paper's Limitations chapter. What's
> still open, what's known broken, what's been observed but
> not proven, what's been hypothesized but not tested. The
> honest counterweight to the thesis + evidence chapters'
> claims.

## What counts as a limitation here

This chapter distinguishes four classes of limitation, each
with a different epistemic shape:

| Class | Shape | Examples |
|---|---|---|
| **Substrate gap** | Known failure mode with a filed fix (often in roadmap). | b3f440c8 cluster; Caterpillar's static blindspot. |
| **Scope-bounded validation** | Claim holds in the spec'd use case but would fail outside it. | B1 + C2 from code-quality artifact (latent at v1, acute at v2). |
| **Sample-size limit** | N is too small to support a stronger claim than "observation with mechanism." | N=2 pilots; one directive class; one model class. |
| **Missing rigor** | Comparison or eval that would strengthen the claim hasn't been run. | P7 generic-baseline eval; single-shot Haiku/Sonnet comparison baselines. |

What goes in **future work** instead of here: things that are
genuinely future work (the comparative pilot experiment
68a882b3; productionization of the autonomy progression beyond
Tier 2; guest casts like Holmes/Watson getting workflow
shapes). Limitations is what's *currently* unresolved; future
work is what's *planned*. Some items appear in both
chapters with different framings.

What does NOT belong here: aspirational features (those live
in roadmap), tactical bugs (those live in the issue tracker
or get fixed without a chapter mention). The discipline of
this chapter: each limitation gets named, scoped, and either
linked to its filed fix or framed honestly as an open
question.

---

## Substrate gaps

### The "prior-milestone-awareness" cluster

The mvp-demo2 Tier 2 pilot surfaced four substrate gaps that
share a single theme: **the substrate has limited awareness
of prior-milestone shipped work at different layers**. Each
layer (review, consolidation, design framing, coverage check)
has its own gap, and the gaps interact — fixing one without
the others leaves partial coverage of the underlying issue.

The cluster, in roadmap-item form:

**b3f440c8 — Caterpillar M8 sibling-feature visibility.**
Today Caterpillar reviews one feature in isolation; he sees
its implementation, tickets, contracts, ADRs but NOT sibling
features (under the same milestone or adjacent ones) that
might be responsible for filling the gap he's flagging.
Result: false-positive findings of the shape *"this code
doesn't handle X"* when feature B is going to handle X.
mvp-demo2 surfaced this as a pattern; substrate fix is to
seed M8's directive with a structured sibling-feature
summary.

**4a2597a4 — Cross-feature consolidation aware of shipped
features.** T-a5 cross-feature consolidation clusters tickets
across features currently in design but misses the case
where current-design produces a feature that duplicates work
in a shipped/verified feature from a prior milestone.
mvp-demo2 surfaced this when Rabbit composed a "markdown
rendered preview" feature during M2 design despite M1 having
already shipped `MarkdownPreview.tsx`. The existing-code
block surfaced the file but Rabbit interpreted it as "might
need extension" rather than "already done."

**81af78f8 — Two-tier feature presentation in design context.**
The tradeoff mvp-demo2 surfaced: when `_load_features` filters
by primary milestone (to prevent Rabbit debating
prior-milestone features in M3 composition), Rabbit loses the
"what already exists" signal and overshoots into
adjacent-milestone scope (composed tags/search features
during M3 design despite M2 having shipped them). The two
purposes were entangled in the original unfiltered design —
preventing wedge vs preventing overshoot. Fix: split into
active-milestone (composable seed pool) + sibling-milestone
(passive "ALREADY SHIPPED, DO NOT REDESIGN" block).

**e7d226b8 — Coverage check aware of existing implementations.**
The `milestone_realization` check only counts a requirement
as realized when a NEW feature in this design pass sources
stories realizing it. Doesn't recognize that prior-milestone
implementations (verified features + shipped code) already
satisfy a requirement. mvp-demo2 M3 surfaced this: M3's
consumes_requirements included a validation criterion
embedding capability names (tag, search, persist); the
coverage check pressured Rabbit to compose M2-overlapping
features. Fix: extend `compute_unrealized_milestone_requirements`
to also check VERIFIED features from prior milestones.

### What the cluster means

The four items aren't independent bugs. They're four
expressions of one underlying gap: **the substrate's model of
"prior-milestone shipped work" is partial at every layer**.
Each layer's piece works in isolation but the layers don't
compose into a coherent picture for the agents to read.

This is itself methodologically interesting (per the
[methodology chapter source](./methodology-chapter-source.md)):
the *cluster recognition* is the work, not the individual
fix-filing. Each item could be filed and fixed
independently and the underlying issue would partially
persist. The right next-pilot loop addresses the cluster as
a structural addition — *"the substrate has a coherent model
of prior-milestone shipped work, exposed at every layer that
needs to read it"* — not four separate point fixes.

Honest scope: until the cluster fix ships, mvp-demo2's
operator gate-approver work included skipping the duplicate
features at queue time. That's not Tier 3 (substrate state
edit), but it IS attention the operator was paying that a
mature substrate wouldn't need. The Tier 2 autonomy claim is
qualified by this — the substrate needed the operator's
skipping discipline at gate points to ship cleanly.

### Adjacent: stronger contextual signal per phase

Three roadmap items share a related theme — *"agents need
stronger contextual signal per phase"* — but at a different
layer than the cluster above:

- **79ef174a — Persona-anchoring in milestone-plan.** The
  tdd-design entry meeting prepends a milestone-framing
  block that names the active persona; milestone-plan has no
  equivalent. Alice gets confused about persona during
  milestone-plan. Surfaced in mvp-demo2; small directive
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
  Operator's observation during mvp-demo2: *"putting features
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

Per
[`project_mvp_demo_m1_m2_overlap.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_mvp_demo_m1_m2_overlap.md):
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

## Known model-class limits

### Caterpillar's static blindspot

Per
[`project_caterpillar_static_blindspot.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_caterpillar_static_blindspot.md):
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

Per the [code-quality artifact §6.2](./code-quality-mvp-demo2.md#62-c2-cross-endpoint-serialization-mismatch--failure-mode-of-m8-static-review):
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

Scope honesty: this finding is latent in mvp-demo2's spec'd
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

## Sample-size limits

The chapter should be explicit that current evidence has
sample-size limits that bound what claims can be made.

### N=2 pilots end-to-end

Wonderland has run **two end-to-end pilots** that reached
shipped-artifact state: mvp-demo (partial completion,
substrate-immature, ~$40 of substrate-fixer interventions)
and mvp-demo2 (complete, Tier 2 autonomy, $83.78, one
mid-pilot substrate fix). Earlier work (P1-P19) tested
substrate primitives but not end-to-end pilots.

What N=2 means for the claims:

- **The mechanism is predictive even at low N.** Each
  pillar in the evidence chapter is framed as
  "observation + mechanism" — the mechanism makes the
  pillar falsifiable in future pilots even at current
  sample size. (Quality-cost coupling will recur because
  the mechanism predicts it; if it stops recurring, the
  mechanism needs revisiting.)
- **No statistical claims.** The chapter should not frame
  any claim as "across N pilots, X% of the time…" — N=2
  doesn't support that shape.
- **Future pilots strengthen specific claims.** Each pilot
  adds observations to each pillar; the mechanism gets
  stronger or gets refuted; the pillar's framing tightens.

### One directive class (notebook-shaped)

Both mvp-demo and mvp-demo2 used variants of the
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

Per
[`project_workflow_variants.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_workflow_variants.md):
the workflow YAMLs are designed to be atomic and
composable; Dodo dynamically chaining workflows for
different work shapes (incident response, security audit,
hotfix) is the architectural direction. But the chaining
infrastructure isn't built yet; the pilots that would
validate cross-shape transferability haven't run.

### One model class (Haiku 4.5)

All claims are at `claude-haiku-4-5-20251001` substrate
version 0.8.0. The Haiku-as-thesis-statement framing (per
[`project_haiku_thesis.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_haiku_thesis.md))
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

## Missing rigor

### P7 generic-baseline eval is future work

The thesis chapter's Corollary 1 (small models outperform
expected capabilities via identity) makes a specific
predictive claim: a Haiku-class model with strong
constitution should hold its own against a large model with
a generic prompt. **This is exactly the kind of claim a
research paper should test rigorously.** It hasn't been
tested.

The P7 eval harness — generic-baseline-vs-identity-native
on matched tasks — is on the roadmap but not built. Until
it ships, the strongest empirical claim is *"Haiku produces
work consistent with what identity-bearing-the-work would
predict,"* not *"Haiku outperforms generic-prompt-on-Haiku."*
The chapter should be explicit about this gap.

### Comparison baselines for code quality

Per the [code-quality artifact §8](./code-quality-mvp-demo2.md#8-comparison-baselines-recommended-follow-up):
the artifact's quality claims are graded against an
independent reviewer's professional standards. To close the
rigor loop, the paper should establish a baseline showing
what code *without* Wonderland looks like for the same
directive. Three recommended experiments (single-shot Haiku,
single-shot Sonnet, OSS notebook contrast) are described as
future work, not yet run.

What's been claimed: Wonderland-on-Haiku produces code an
independent reviewer reads as *"competent, above-average
code for an MVP."* What hasn't been claimed: that it
out-performs Haiku-without-Wonderland or
Sonnet-without-Wonderland. The honest framing is that
Wonderland's output is review-grade; the comparative
question is open.

### Untested hypothesis: Haiku as architecturally optimal

Per
[`project_haiku_is_architecturally_optimal.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_haiku_is_architecturally_optimal.md):
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

## Tier 2 scope limits

mvp-demo2 was the first pilot at Tier 2 autonomy (per
[`project_first_tier2_pilot_completion.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_first_tier2_pilot_completion.md)).
Several limitations follow:

### One pilot at Tier 2

N=1 at the Tier 2 autonomy level. The substrate's claim is
"can run Tier 2 on notebook-class directives at substrate
0.8.0." The chapter shouldn't claim Tier 2 readiness as a
general property; the next 2-3 pilots will either confirm
or refine the autonomy claim.

### Operator gate-approver discipline is qualitative

The Tier 2 distinction (gate-approver vs fixer) is named
operationally but isn't yet measured with rigor. mvp-demo2's
operator interventions were documented:

- 1 substantive scope clarification (full-text vs tag-only
  search).
- Multiple duplicate-feature skips at gates.
- Ticket-level scope filtering on M3's megalith feature.
- 1 mid-pilot substrate fix (the Tier 2 violation).

The categorization "queue decisions ARE gate-approver work"
draws a line that's defensible but not formal. A future
methodology paper might propose a quantitative measure
(intervention frequency × intervention depth × substrate-state
impact); current paper should describe the
qualitative discipline honestly without dressing it as
metric.

### Mid-pilot substrate fix as Tier 2 violation

The auto-directive synthesis shipped mid-pilot is, formally,
a Tier 2 violation: substrate code changed during the pilot.
The methodology chapter argues this is honest documentation
of iterative substrate maturity (better than pretending the
pilot ran on the substrate version that started it). The
limitations chapter should re-acknowledge: **mvp-demo2's
completion required one Tier 2 violation**. A future pilot
that completes with ZERO mid-pilot substrate changes would
be a stronger autonomy claim. That pilot hasn't run.

---

## What the limitations DON'T defeat

The honest framing of limitations is part of the paper's
credibility, but it shouldn't undersell what HAS been
demonstrated. Per the evidence chapter:

- **Quality-cost coupling held across every substrate
  iteration to date**, even if N=2 at pilot level.
- **Zero hallucinated findings in 7+ Caterpillar reviews on
  Haiku 4.5** — schema-as-safety works on small models.
- **mvp-demo2 shipped a working full-stack artifact for
  $83.78** at Tier 2 autonomy — the substrate's first
  end-to-end Tier 2 completion.
- **The substrate evolved through pilot-driven discovery**
  — each pilot surfaced the next layer of failure modes;
  most got categorized + addressed before the next pilot.

The limitations are framed against these — not as defeating
them but as bounding them. The thesis is *"identity does
real work, demonstrated at this scale on this directive
class with this model"*, not *"identity solves multi-agent
systems."* The bounded scope IS the credibility.

---

## What's NOT in this chapter

Goes in **future work** instead:

- **68a882b3** — design-all-first vs interleaved
  comparative pilot. Filed; not yet run.
- **Holmes/Watson cast workflow shapes** — guest cast
  exists; workflow that convenes them doesn't.
- **Dodo dynamic orchestration** — atomic workflow chaining
  for different work shapes (incident response, security
  audit). Architectural direction; not built.
- **Productionization of Tier 3 autonomy** — if Tier 2
  holds across more pilots, the eventual question is
  whether the substrate can self-modify (a substrate fix
  shipped BY the agents during a pilot, not by the operator).
  Long-range; not currently active.
- **Branching memory limits** — branching held in
  mvp-demo2 but N=1 at the architectural level. Future
  pilots may surface its own failure modes (cross-branch
  context loss for genuinely cross-milestone reasoning, etc.).
- **Workflow YAML composability** — current workflows are
  atomic in shape but not yet dynamically composable at
  runtime; the chaining infrastructure (29497820 in
  roadmap) is architectural direction.

Goes in **methodology** instead:

- How limitations get surfaced + categorized
  (categorization-through-failure discipline).
- How the loop between pilot → categorization → substrate
  → next pilot continues to operate.

Goes in **code quality artifact** instead:

- Specific reviewer findings (B1, C1-C8 from cold review)
  with line citations. The limitations chapter cites the
  artifact rather than duplicating.

---

## See also

- [Methodology chapter source](./methodology-chapter-source.md)
  — the discipline through which limitations get surfaced
  + categorized.
- [Evidence chapter source](./evidence-chapter-source.md) —
  the claims these limitations bound.
- [Thesis chapter source](./thesis-chapter-source.md) — the
  corollaries each limitation tempers.
- [Code quality artifact](./code-quality-mvp-demo2.md) —
  the artifact-level limitations (B1, C2, frontend tests,
  etc.) cited above.
- Roadmap items cited:
  - 79ef174a, b3f440c8, 4a2597a4, 81af78f8, e7d226b8 —
    prior-milestone-awareness cluster + persona-anchoring.
  - 68a882b3 — design-all-first vs interleaved (future work).
  - 837b5bbb — feature sequencing with depends_on.
  - 124b5858 — auto-directive synthesis (shipped mid-pilot).
  - 29497820 — Dodo dynamic orchestrator (future work).
- Memory observations cited:
  - `project_mvp_demo_m1_m2_overlap.md` — milestone-boundaries
    advisory pattern.
  - `project_caterpillar_static_blindspot.md` — known
    blindspot with shipped fix.
  - `project_substrate_fixes_dont_propagate_through_memory.md`
    — memory-bleed counterexample to convergent self-repair.
  - `project_haiku_is_architecturally_optimal.md` — untested
    hypothesis explicitly marked.
  - `project_workflow_variants.md` — atomic-workflow
    direction (future work).
  - `project_first_tier2_pilot_completion.md` — Tier 2
    autonomy claim + intervention log.
