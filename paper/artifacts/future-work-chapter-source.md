# Future work chapter source

> Source material for the paper's Future Work chapter. What
> the next iteration loops will test, what comparative
> experiments would strengthen the existing claims, what
> architectural directions are filed but not built, and what
> research questions the project's findings open up beyond
> Wonderland itself.

## What counts as future work here

This chapter distinguishes three classes of future work, each
with a different shape and time horizon:

| Class | Shape | Time horizon |
|---|---|---|
| **Near-term substrate evolution** | Filed roadmap items + cluster fixes with clear scoping. The next 1-3 pilot loops. | Weeks to a few months. |
| **Comparative experiments** | Eval harnesses + baseline runs that would close the rigor loop on existing claims. | Cost-bounded; tractable now. |
| **Research-direction questions** | Architectural shifts (Tier 3 autonomy, self-hosting), guest casts that don't yet have workflow shapes, identity engineering as a discipline beyond Wonderland. | Months to years; some genuinely open. |

What DOESN'T go here: items that are limitations (those have
their own chapter); aspirational marketing ("could be
applied to anything"); reactive bug-fixing. Each future-work
item should name what it tests, what it would resolve from
the limitations chapter, and what evidence it would produce
for the paper's next iteration.

The relationship to other chapters:
- **[Limitations chapter](./limitations-chapter-source.md)** —
  many limitations have filed fixes; the fixes are this
  chapter's near-term substrate evolution section. Limitations
  + future work form a tight pair: limitations name what's
  open, future work names how it gets closed.
- **[Thesis chapter](./thesis-chapter-source.md)** — each
  corollary makes predictive claims; future work includes the
  experiments that would falsify or strengthen them.
- **[Methodology chapter](./methodology-chapter-source.md)** —
  future work is what feeds the pilot → categorization →
  substrate → next pilot loop's next cycle.

---

## Near-term substrate evolution

### The prior-milestone-awareness cluster fix (b3f440c8 et al.)

Per the limitations chapter, four roadmap items share one
underlying gap: the substrate's model of "prior-milestone
shipped work" is partial at every layer. The next substrate
pilot loop should treat this as a *cluster fix* — one
structural addition that resolves the cluster — not four
point fixes.

The structural addition: **a coherent shipped-work model
exposed at every layer that needs to read it.**

- At the **design framing layer** (81af78f8) — sibling-milestone
  features in a passive "ALREADY SHIPPED" block, active-milestone
  features in the composable seed pool.
- At the **composition layer** (4a2597a4) — cross-feature
  consolidation aware of shipped features, not just current
  design tickets.
- At the **review layer** (b3f440c8) — Caterpillar M8 seeds
  sibling-feature summaries so coherence-reading covers the
  landscape, not just the slice.
- At the **coverage check layer** (e7d226b8) — milestone
  realization check counts prior-milestone shipped features
  as realizing the current milestone's overlapping requirements.

**What this fix would test:** whether mvp-demo3 (or whichever
pilot follows) needs the operator's duplicate-skip discipline
at gate points. If the cluster fix holds, operator Tier 2
interventions drop to ~zero on the next notebook-class pilot.

**Paper consequence:** the Tier 2 autonomy claim tightens.
Currently "Tier 2 with operator gate-approver discipline on
duplicate-skipping"; after the cluster fix, "Tier 2 with
operator gate-approver discipline on transition approval
only." That's a stronger autonomy claim.

### Feature sequencing with depends_on (837b5bbb)

Operator observation during mvp-demo2: *"putting features in
an order would as a byproduct result in more tightly
designed features."* The constraint (an explicit dependency
between features) would force Rabbit during M2 composition to
think about ordering, tightening scope per feature.

This is a Pillar-5 prediction (constraints improve quality):
adding `Feature.depends_on: list[feature_slug]` should both
tighten output AND lower per-feature cost. The pilot that
ships it would test the prediction.

Related: extends `existing-code-awareness` block — design for
feature N could see code from N's dependencies (which have
already shipped). Partially resolves b3f440c8 (Caterpillar's
M8 could reason "feature N depends on X which is shipped").

### Persona-anchoring in milestone-plan (79ef174a)

mvp-demo2 surfaced this: Alice gets confused about persona
during milestone-plan because the meeting has no persona-anchor
block (tdd-design's entry meeting has one; milestone-plan
doesn't). Small directive edit, substrate-side helper
mirroring the existing pattern. Belongs in next p20 follow-up
batch.

### Frontend test enforcement loop

Per the code-quality artifact: `vitest` is installed but zero
frontend tests exist because there's no substrate enforcement
loop. The shaped fix:

- M9 gains an `npm_test` build-check parallel to
  `pytest_passes` + `npm_build`.
- M7's directive gains an explicit requirement that the
  Hatter scenarios for this ticket exist as runnable tests
  in the appropriate test directory.

**What this would test:** whether the substrate's
constraint-improves-quality property extends to the test
discipline domain. Backend tests get written because
`pytest_passes` exists; the same enforcement loop on frontend
should produce equivalent discipline. If it does, that's
additional Pillar-5 evidence.

### Cross-endpoint scenario coverage as Hatter M6 prompt

The C2 finding from the code-quality artifact (revision_id
serialization mismatch across endpoints) is invisible to M8's
per-file coherence review. The right-sized fix is at M6:
Hatter's scenario-generation prompt explicitly includes
**cross-endpoint round-trip scenarios** as a first-class
class — "client lists notes, picks one's revision_id, PUTs
with that revision_id, expects 200."

**What this would test:** whether C2-class bugs become
substrate-visible at M6, surface as failing tests at M7, and
get fixed before reaching the verified artifact. The
underlying claim is that the M6 → M7 → M9 loop can catch
cross-endpoint behavioral bugs if Hatter generates the right
scenarios.

---

## Comparative experiments (the rigor expansion)

The evidence chapter is honest about what hasn't been
measured rigorously. Several comparative experiments would
close that loop. Each is cost-bounded and tractable to run
now.

### Single-shot Haiku / Sonnet baselines for code quality

Per the [code-quality artifact §8](./code-quality-mvp-demo2.md#8-comparison-baselines-recommended-follow-up):

- **Single-shot Haiku 4.5 against the notebook directive.**
  Cheapest (~$0.20-0.50). Give Haiku the literal directive
  in one inference, capture the artifact, compare line by
  line to mvp-demo2's demo/. Hypothesis: 2-3 file sketch,
  no test coverage, no security helpers,
  `dangerouslySetInnerHTML` without sanitization.
- **Single-shot Sonnet 4.6 against the notebook directive.**
  The harder rebuttal (~$1-2). Hypothesis: shape-comparable
  CRUD but lacks multi-lens discipline (no anti-bypass
  docstrings, no severity-tagged tests, no cross-file
  contract citations). Cleaner-on-surface,
  lower-discipline-on-inspection.
- **OSS markdown-notebook contrast.** Find an existing OSS
  hobby project of comparable scope; read its security
  discipline + test coverage + contract clarity. Free; just
  reading.

**What each tests:** Pillar 1 (quality-cost coupling) on
*absolute* code-quality terms, not just substrate-iteration
terms. If single-shot Sonnet produces equivalent-quality
code at lower cost, the substrate's value proposition
weakens; if Sonnet produces shape-comparable but
discipline-lower code, the multi-lens-review thesis holds at
the comparative level.

### Agentic-vs-agentic baselines — artifact density per agent-tax dollar

The single-shot baselines above test the *cheapest possible
competitor* to Wonderland. The category that's structurally
closer to Wonderland but hasn't been probed is *other
agentic / multi-step coding systems*: Devin, Cursor Agent,
Aider, Claude Code used as a project orchestrator. These
systems share Wonderland's property of paying an agent
tax — VM startup, codebase exploration, planning passes,
test iteration, multi-turn deliberation — that scales with
agent structure, not task complexity. On a small directive,
all of them look bloated relative to single-shot for the
same category-level reason. (See the
[comparison-baselines analysis](./comparison-baselines/README.md#what-kind-of-comparison-is-this--single-shot-vs-wonderland-is-the-cheapest-possible-framing)
for the framing of why notebook-class inefficiency is a
category property, not a Wonderland-specific weakness.)

**Shape of the eval:** Run Devin (or Cursor Agent, or Aider,
or Claude Code-as-orchestrator) against the same notebook
directive. Measure not just cost + working-code, but
*artifact density per dollar* — what reusable byproducts
does each system produce alongside the code? Wonderland's
hypothesis is that within the agentic-system category, the
substrate produces structurally more artifacts (typed
tickets / features / stories, ADRs, contracts, FindingKind-
typed reviews, 5-hop decision trails, JSONL audit logs) for
the same agent-tax dollar than session-log-only systems
do. Most agentic-coding evaluations measure "did the code
work" and "how much did it cost"; neither captures what
the tax pays for in terms of downstream maintainability.

**Why this matters for the paper:** the comparison-baselines
analysis's biggest framing blind spot is that it positions
Wonderland against the cheapest baseline. A reader sympathetic
to agentic coding (the right audience for "you *can* do this")
will reasonably ask: *"OK, but what's Wonderland buying me
relative to Devin or Cursor Agent, not relative to
`claude -p`?"*  The answer is artifact density per dollar of
overhead you're already paying — which is a defensible claim
once measured, but which the current data doesn't
substantiate. Filing as a near-term comparative pilot rather
than long-horizon research because the eval design is
tractable: one notebook directive, four agentic systems, 4-8
hours of operator time per system, ~$50-200 total spend
across all of them.

**What this tests:** that Wonderland's structural artifact-
production isn't redundant with what any agentic coding
system already produces. If Cursor Agent's session logs +
plan files cover 80% of Wonderland's artifact trail, the
substrate's distinctive value compresses. If they cover 20%,
the typed-artifact thesis holds at the comparative level.

### P7 generic-baseline-vs-identity-native eval

The thesis chapter's Corollary 1 (small models outperform via
identity) makes a specific predictive claim. The P7 eval
harness would test it rigorously: same task, same model,
two conditions (generic prompt vs identity-native
constitution).

**Shape of the eval:** matched-on-task comparisons across a
batch of representative directive shapes (CRUD endpoint
implementation, story decomposition, code review, test
scenario generation). Each task gets graded on a rubric
(correctness, edge-case coverage, named tradeoffs, etc.).
Comparison: identity-native vs generic-prompt-on-same-model.

**Roadmap item exists** (P7); harness not built. The
limitations chapter is explicit that until P7 ships, the
strongest Corollary 1 claim is "Haiku produces work
consistent with what identity-bearing-the-work would
predict," not "Haiku outperforms generic-prompt-on-Haiku."

### Design-all-first vs interleaved comparative pilot (68a882b3)

Current Wonderland pattern (interleaved): milestone-plan →
design M1 → implement M1 → design M2 → implement M2 → ... →
integration. Proposed alternative (design-all-first):
milestone-plan → design ALL milestones → implement M1 → M2
→ ... → integration.

Run the same project (the notebook directive) both ways;
compare cost, quality, wedge count, operator-intervention
frequency.

**Hypothesis:** design-all-first addresses b3f440c8
(Caterpillar sees full sibling-feature landscape during
review) and gives cleaner cross-feature consolidation, but
loses the iterative-discovery feedback loop where impl
reveals design needs.

**Paper deliverable:** A/B comparative cost + quality data
for the two sequencings, with discussion of which pattern
works better for which project shapes. This is a comparative
pilot that produces NEW evidence; not just baselining
existing claims.

### Cross-model comparative pilots

The Haiku-architecturally-optimal hypothesis (per
[`project_haiku_is_architecturally_optimal.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_haiku_is_architecturally_optimal.md))
is currently UNTESTED. The operator's qualitative read: Opus
might *under-perform* Haiku on Wonderland because the
substrate's constraints are calibrated for Haiku's
capability shape.

The test: run mvp-demo3 (same notebook directive, same
substrate version) on Opus instead of Haiku. Compare cost,
quality, wedge patterns, character behavior.

**Hypothesis directions** (any of which would be paper-worthy):
- Opus performs better than Haiku (the conventional
  expectation — larger model, more capability).
- Opus performs equivalently to Haiku at higher cost (the
  "identity does the work, model class doesn't matter as
  much" prediction).
- Opus performs WORSE than Haiku (the operator's qualitative
  observation — Opus over-reasons against constraints
  calibrated for smaller capability).

Each outcome is informative. The third would be the most
surprising and the most thesis-relevant.

---

## Cross-shape transferability

mvp-demo + mvp-demo2 both used variants of the "personal
markdown notebook web app" directive. The substrate's
properties haven't been tested on:

### Different directive classes

- **CLI tools** — the `runtime: cli` substrate framing
  exists; the M5 contract-negotiation directive translates
  Tweedle roles for the runtime; no pilot has shipped one.
- **TUI projects** — same as CLI; substrate is ready, no
  pilot.
- **Backend-heavy projects** (services, daemons, background
  workers) — no UI surface; would test whether the
  full-stack-frontend-heavy pilot data generalizes.
- **Mobile / desktop apps** — substrate isn't yet shaped for
  React Native / Electron / native; would require new
  skeleton + workflow adaptations.
- **Domain-specific shapes** — data pipelines, ML systems,
  scientific computing. These have different artifact
  shapes (notebooks, DAG configs, etc.) that may need new
  agent identities or workflow shapes.

The forward question: **does the substrate transfer cleanly
across directive classes, or does each class need
substantial adaptation?** Current architecture predicts
clean transfer (workflows are atomic; characters are stable;
runtime field adapts roles); the prediction hasn't been
tested at pilot scale.

### Different model classes

Wonderland defaults to `claude-haiku-4-5-20251001`. The
substrate has been smoke-tested on Sonnet during development
work (mostly coding sessions) but no full pilot has run on
non-Haiku. The cross-model comparative pilots above (Opus
on the same directive) start here; the deeper question is
whether non-Anthropic models support the same
identity-engineering discipline.

The architectural prediction: identity engineering works on
any model that can sustain in-character reasoning over long
contexts. Practically, this means models with strong
constitution-following at the system-prompt level. The test
hasn't been run; it's a future pilot's input.

### Atomic workflow composability

Per
[`project_workflow_variants.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_workflow_variants.md):
the architectural direction is **workflows as atomic,
composable units that Dodo dynamically chains at runtime**.
Pattern chaining in a music sequencer is the right metaphor.
The build pipeline (canonical/tdd) is one chain; an
incident-response pipeline (Holmes/Watson finding /
verifying bugs, Moriarty red-teaming) would be a different
chain Dodo dispatches when something goes wrong.

Most directives mix and match — a feature with a
security-critical surface might chain
`tdd` → `holmes-watson-review` → `moriarty-redteam` →
`caterpillar-final`.

**Roadmap item 29497820** (Dodo as dynamic meeting
orchestrator) is the architectural ask. The unit of
composition becomes the workflow, not the meeting. Workflows
become atomic via the existing YAML format; Dodo gains
selection + chaining logic.

What this would test: whether the substrate scales to
arbitrary multi-workflow compositions, or whether
cross-workflow seams introduce new failure modes.

---

## New cast capabilities

### Holmes / Watson workflows (incident response, security audit, codebase backfill)

Per
[`project_holmes_cast.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_holmes_cast.md)
and the [cast walkthrough](./cast-walkthrough.md): Holmes +
Watson is the framework's first guest cast — asymmetric pair
(Holmes leads investigation, Watson translates +
interrogates). Constitutions shipped; no workflow yet convenes
them.

The anticipated workflow shapes:

- **discovery-backfill** — Holmes infers requirements from
  existing project state rather than interviewing the
  operator. Use case: an existing codebase that needs
  Wonderland framing added. Watson translates Holmes's
  findings into the requirement artifacts that
  milestone-plan can seed from.
- **incident-investigation** — Holmes reads incident
  artifacts (logs, telemetry, recent commits); Watson
  translates findings for Queen (security framing) and
  Tweedles (remediation work).
- **security-audit** — Holmes maps the codebase's actual
  attack surface; Watson translates for Queen's threat
  modeling. Output: an updated Threat Garden + Queen
  rulings on found gaps.

Each workflow's design is a separate piece of work. The
Watson-as-translator role is constitutive of the workflow's
output shape (different receiving agents → different
translations); the architecture is ready.

### Other guest casts that might emerge

The Holmes/Watson asymmetric-pair model opens a door. Other
shapes might fit:

- **Moriarty** (mentioned in the workflow-variants memory)
  — a red-team adversarial character. Pairs with Queen for
  security work; could pair with Hatter for adversarial
  scenario generation in particularly safety-critical code.
- **A historian character** — reads git history + analyses/
  + memory observations for cross-pilot trend analysis.
  Would help long-running projects develop a sense of
  trajectory beyond individual pilots.
- **A documentation specialist** — translates the artifact
  trail into operator-facing prose (the project currently
  uses analyses/ for this; a dedicated character with §IV
  shape constraints might produce different shape).

These are speculative; each would need a constitution shaped
around its characteristic failure mode + persistence
artifact + relational defaults. The architectural commitment
is that adding a character has cost (per the cast
walkthrough §"The cast is small on purpose"), so each
addition should earn its slot rather than fit aspirational
roles.

### Pair protocols as a primitive

The Tweedle pair (symmetric) and Holmes/Watson pair
(asymmetric) are the only two pair-shaped identities so far.
The architectural direction worth exploring: **pair protocols
as a first-class primitive**. Other shapes might fit:

- **Mentor / apprentice** — asymmetric pair where the
  apprentice is in-character learning the mentor's
  discipline. Could model character evolution over long
  projects.
- **Adversarial pair** — Hatter + Queen as a unit, with the
  explicit role of producing devil's-advocate review on
  designs.
- **Lateral peer pair** — two agents of equal authority
  whose disagreement is the work (similar to Tweedles but
  for different domains, e.g., the architect + the
  reviewer arguing over a structural choice).

The pair-protocols infrastructure
(`tweedle_pair_protocol.md`, `baker_street_protocol.md`)
exists; what's missing is the substrate machinery that lets
pairs be a configurable choreography element in workflows.

---

## Architectural research questions

These are larger-horizon questions the project's findings
open up. Some are tractable in the next 6-12 months; some
are genuinely long-range.

### Tier 3 autonomy — what does substrate self-modification look like?

The autonomy ladder so far:
- Tier 1 — operator observes; substrate runs.
- Tier 2 — operator gate-approves; substrate runs + ships.
- Tier 3 (current definition) — operator designs / edits
  substrate state.

The methodology chapter framed Tier 3 as "the substrate's
baseline before specific gaps are closed." But there's a
*forward* Tier 3: a substrate that can **self-modify** — a
substrate fix shipped BY the agents during a pilot, not by
the operator. The mid-pilot substrate fix in mvp-demo2 was
operator-shipped; Tier 3-forward would have the agents
recognize the gap, propose the fix, and ship the substrate
change.

This is **genuinely long-range**. Requirements:
- A constitution shape for an agent whose role is substrate
  development (maybe a guest cast).
- Substrate-modifying tools exposed under stricter constraints
  than current code-modifying tools.
- A meta-workflow that fires when the runtime detects a
  pattern matching a previously-categorized failure mode.

The research question: **can identity engineering scale to
identities whose work IS the substrate?** Wonderland-built
agents currently build apps; could they also build the
substrate that builds them? This connects to:

### Self-hosting — "Wonderland building Wonderland"

The operator's stated long-range goal during mvp-demo2:
*"once we're ready I definitely want to try building
wonderland with wonderland."* The fixed-point question:
can the substrate produce the next version of itself?

Doing this right is harder than it sounds. Wonderland's
constitutions, workflow YAMLs, substrate primitives, and
analysis discipline are interrelated; changing any one
affects the others. A self-hosting attempt is a
**categorically different kind of pilot** from a notebook
app — the directive's output IS the substrate that
processed the directive.

Research questions surfaced:
- Can the substrate's own complexity be expressed in
  Wonderland-shaped artifacts (stories about substrate
  needs, tickets that touch substrate code, reviews of
  substrate changes)?
- Does identity engineering hold up when the agents are
  designing for themselves (would they over-constrain or
  under-constrain)?
- What's the right way to bootstrap — a self-hosting pilot
  needs an existing substrate to run on, so the first
  iteration is necessarily operator-shipped; what does the
  second iteration look like?

This is the project's most ambitious long-range research
direction.

### The interviews + milestones layer as a long-running collaboration substrate

Per
[`project_interviews_milestones_thesis.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_interviews_milestones_thesis.md):
the Interviews + Milestones structural layer makes
Wonderland a *long-running collaboration tool* rather than a
series of one-shot generation passes. Discovery captures
intent once; milestones organize requirements into a
multi-run trajectory; design iterations operate within a
milestone scope.

The forward question: **what does Wonderland look like as a
substrate that supports projects across months or years**,
not just weeks? Current pilots are end-to-end realizations
of a notebook-sized directive in days. Longer-horizon work
shapes:

- **Multi-month projects** — multiple discovery rounds as
  the directive's intent shifts; milestone amendments;
  branching trajectories.
- **Team-shaped operators** — multiple operators
  collaborating on the same project; how do gate-approval
  decisions distribute? How does the substrate handle
  multi-operator disagreement?
- **External-stakeholder integration** — non-operator
  consumers of the artifact trail (e.g., compliance
  reviewers reading the audit log, product managers
  reading milestone summaries).

The substrate primitives ready for this scale: branching
memory, Mock Turtle consolidation, audit log infrastructure,
interview-driven requirement amendment. The primitives that
might not scale: per-agent memory storage (currently
disk-resident per agent, may need shared store for team
operators); telemetry surface (currently single-run; would
need cross-run aggregation).

---

## Identity engineering as a research discipline

The project's broader contribution beyond Wonderland itself
is the case for **identity engineering** as a research
discipline distinct from prompt engineering, agent
engineering, or multi-agent systems work.

Per the [thesis chapter](./thesis-chapter-source.md#the-connection-to-identity-engineering-as-a-discipline):

> Identity engineering is the discipline; Wonderland is one
> instance; the paper is the case for the discipline being
> worth pursuing beyond this instance.

What this means for future research:

### Identity engineering beyond Wonderland

Wonderland's cast is named after Carroll characters because
literary characters carry intentions in a way "the X agent"
doesn't. Other identity-engineering instantiations might
use different cast frames:

- **Industry-shaped casts** — medical professionals
  (attending, resident, intern; each with characteristic
  failure modes) for medical AI applications.
- **Discipline-shaped casts** — academic peer review (the
  reviewer, the author, the editor; each with characteristic
  failure modes) for research assistance.
- **Domain-shaped casts** — engineering disciplines
  (mechanical, electrical, software; each with characteristic
  failure modes) for cross-discipline design work.

The research question: **what makes a cast frame work?** The
Carroll cast works because the characters are recognizable
(literary tradition), have internal contradictions (each
character's virtue + characteristic failure), and don't
overlap (Alice ≠ Rabbit ≠ Cat). What's the formal version
of those properties that would let practitioners design new
casts from scratch?

### Failure-modes-as-identity outside literary framing

The §VIII pattern uses the Sephirah/Qlipha pairing analogy
(per the thesis chapter Corollary 2). Each virtue arrives
with its named shadow. Could the pattern be expressed
without the literary framing?

The research question: **is the literary framing
load-bearing for the pattern, or is it scaffolding that
practitioners could replace with formal constructs?** The
operator's intuition is that the literary framing IS
load-bearing — characters carry intentions; roles don't.
Testing this would require building a substrate parallel to
Wonderland with role-based agents (no character framing)
but the same §VIII discipline (each role has a named
characteristic failure mode), and comparing.

### Pair protocols as a primitive worth studying

The Tweedles' symmetric pair and Holmes/Watson's asymmetric
pair are the only two instances. The research question:
**what's the taxonomy of pair shapes, and which shapes do
which kinds of work better?** This is a richer area than
"more agents = more capability" generally treats — pair
structure (symmetric / asymmetric / lateral / hierarchical)
seems to matter for the work shape, not just the head count.

### Substrate-as-constraint vs prompt-as-instruction

Pillar 5 (constraints improve quality) is currently framed
as a Wonderland observation. The research question:
**does the property generalize?** Does substrate-level
constraint (data shapes, lifecycle states, snapshot
semantics) reliably out-perform prompt-level constraint
(instructions, system prompts) across other agent systems?

Testing this would require building parallel systems —
prompt-only and substrate-constrained — on the same task
class and comparing. It's the kind of comparative study
that would make identity engineering legible to the broader
agent-systems research community.

---

## What's NOT in this chapter

To prevent scope creep when drafting:

| Topic | Lives in |
|---|---|
| Specific reviewer findings + the v1/v2 scope honesty | code-quality artifact §6. |
| The b3f440c8 cluster as a current limitation | limitations chapter. |
| The methodology that produces the next iteration loop's input | methodology chapter. |
| Per-pilot economics + projections | Economics chapter (analysis 033). |
| Mvp-demo2 completion narrative | Wright Brothers chapter (analysis 034). |
| The thesis claims that drive these research directions | Thesis chapter. |
| The five pillars that frame the existing evidence | Evidence chapter. |

The future-work chapter is the *forward-facing* counterweight
to the limitations chapter. Both close the paper honestly:
limitations names what's open; future work names what gets
worked on next + what's research-direction beyond the next
loops. Together they signal that the project knows where it
is in its arc.

---

## See also

- [Limitations chapter source](./limitations-chapter-source.md)
  — what each future-work item would resolve.
- [Methodology chapter source](./methodology-chapter-source.md)
  — the pilot loop that translates future-work items into
  next-pilot inputs.
- [Thesis chapter source](./thesis-chapter-source.md) — the
  corollaries each future-work item would test, strengthen,
  or extend.
- [Evidence chapter source](./evidence-chapter-source.md) —
  the pillars each comparative experiment would close the
  rigor loop on.
- [Code quality artifact](./code-quality-mvp-demo2.md) —
  baseline comparisons recommended in §8.
- Roadmap items cited:
  - 79ef174a, b3f440c8, 4a2597a4, 81af78f8, e7d226b8 —
    prior-milestone-awareness cluster.
  - 68a882b3 — design-all-first vs interleaved comparative
    experiment.
  - 837b5bbb — feature sequencing with depends_on.
  - 29497820 — Dodo dynamic orchestrator (atomic workflow
    chaining).
- Memory observations cited:
  - `project_workflow_variants.md` — atomic workflow
    composability.
  - `project_holmes_cast.md` — guest-cast extensibility +
    asymmetric pair protocols.
  - `project_interviews_milestones_thesis.md` — long-running
    collaboration substrate framing.
  - `project_haiku_is_architecturally_optimal.md` — untested
    hypothesis as candidate for cross-model comparative
    pilot.
