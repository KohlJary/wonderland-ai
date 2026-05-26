# §9 — Future work

## §9.1 — What counts as future work here

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
- **Limitations chapter (§8)** —
  many limitations have filed fixes; the fixes are this
  chapter's near-term substrate evolution section. Limitations
  + future work form a tight pair: limitations name what's
  open, future work names how it gets closed.
- **Substrate evolution chapter (§6)** —
  the chronicle of the iteration cycle that has, to date,
  closed every prior class of limitation it has surfaced.
  Several items previously in this chapter's near-term
  section have closed since the chapter was first written;
  the substrate-evolution chapter documents the closures
  in detail, this chapter cites them briefly as historical
  context.
- **Thesis chapter (§2)** — each
  corollary makes predictive claims; future work includes the
  experiments that would falsify or strengthen them.
- **Methodology chapter (§5)** —
  future work is what feeds the pilot → categorization →
  substrate → next pilot loop's next cycle.

### Status note on cycle progress

This chapter was first drafted at substrate version 0.8.0
when the prior-milestone-awareness cluster (b3f440c8 et al.)
was the load-bearing near-term ask. By substrate version
0.10.2 + T-ab62 + T-ab64, that cluster is substantially
closed (per the limitations chapter's status update on each
item). The chapter has been refreshed to mark closed items
as historical context and to surface the new near-term and
research-direction questions that emerged from the
post-mvp substrate work. The forward-looking sections
(comparative experiments, cross-shape transferability,
identity engineering beyond Wonderland) remain mostly
unchanged because they describe long-horizon work the
substrate evolution has not yet reached.

---

## §9.2 — Near-term substrate evolution

### The prior-milestone-awareness cluster fix (b3f440c8 et al.) — CLOSED

Status update: this near-term item, identified at substrate
0.8.0 (post-mvp pilot), has been closed across the
post-mvp substrate evolution. Per the limitations
chapter, each of b3f440c8 / 4a2597a4 / 81af78f8 / e7d226b8
has been addressed by specific T-ab fixes (T-ab17, T-ab18,
T-ab34, T-ab41, T-ab46, T-ab51 keystone). Validated in the
redux pilot — operator's Tier 2 interventions on duplicate-
feature skips dropped to ~zero, and the per-milestone cost
trajectory ($15.59 → $10.91 → $3.72) is what the cluster
fix predicted: capability milestones building on a stable
foundation, not pressuring against ghost-of-prior-work
deliberation.

The cluster is cited here as **historical context for the
iteration-cycle methodology** — a near-term ask in 0.8.0
became a closed cluster in 0.10.2, with the receipt being
the redux pilot's cost trajectory. The substrate-evolution
chapter documents the per-fix mechanics; this chapter
notes the closure as evidence that the methodology
produces structural closures, not symptomatic patches.

**Paper consequence:** the Tier 2 autonomy claim tightened
as predicted. mvp's "Tier 2 with operator gate-approver
discipline on duplicate-skipping" became, by redux,
"Tier 2 with operator gate-approver discipline on
transition approval only." Three subsequent Tier 2 pilots
have completed without mid-pilot substrate violations.

### Parallel coordination (the wall-clock-time lever)

The substrate currently runs serially — one milestone at a
time; one feature at a time within a milestone; one ticket
at a time within a feature. The cost regime has compressed
to ~$30/pilot for notebook-class directives, but wall-clock
time hasn't compressed at the same rate. A $30 pilot still
takes about an hour to run.

This is what currently bounds Wonderland's competitiveness
on the dimension other autonomous coding systems (Devin,
Cursor Agent, Aider) optimize for. Wonderland has won on
cost + quality + artifact density per agent-tax dollar;
parallel coordination is the move that closes the
wall-clock-time gap.

The substrate's typed-state machinery already supports
parallel orchestration in principle:

- **Per-milestone memory branching** (T-ab8 + T-ab52)
  isolates concurrent milestones — sibling milestones in
  parallel wouldn't pollute each other's deliberation.
- **Feature-level lifecycle states** operate per-feature
  orthogonally across features within a milestone.
- **`gates_on_dependencies` in M7** already supports
  per-ticket dependency gating — tickets whose code
  doesn't depend on other tickets' code can already run
  in parallel within the implement phase.
- **`asyncio.gather` for team_groupings** in meeting.py
  already runs intra-meeting agent windows concurrently;
  the same pattern extends to inter-meeting orchestration.

What's missing is a coordinator that decides "these N
features can run M7 in parallel" based on the dependency
graph, and the orchestration to actually fan them out
across separate runner processes. The work isn't
architectural — it's mechanical. Filed in roadmap;
deferred until template-similarity milestone consolidation
work lands because the two pair multiplicatively
(consolidation maximizes parallelism's surface area).

**What this would test:** whether the substrate's
per-pilot wall-clock time compresses from ~hour to
~10-20 minutes on notebook-class directives. Paper
consequence: closes the most visible competitiveness gap
versus Devin-class systems while preserving the cost +
quality + artifact-density advantages.

### Template-similarity milestone consolidation

Filed observation: when the milestone-plan agent produces
multiple capability milestones with the same architectural
template (consume foundation X → fetch external data →
render on surface Y, with only X/Y/Z varying), the
planner should detect the pattern and consolidate into
one milestone with N features. The LDR pilot's M3 (time),
M4 (weather), M5 (news) cards were the canonical case —
three milestones with identical architectural shape that
should have rolled into one milestone with three sibling
features.

Each near-identical milestone carries fixed-cost overhead
the planner shouldn't be paying:
- 3× milestone-plan reasoning
- 3× tdd-design pass (vs one design pass that produces
  3 features under shared scoping/architecture/composition)
- 3× M9 verify boundary
- 3× memory branch setup

Per-card done-whens become per-feature done-whens. The
consolidation collapses maybe 30-40% of design-side
fixed cost while preserving per-card testability.

**Pairing with parallel coordination:** consolidation
maximizes the surface area parallel coordination applies
to. Sibling features in a consolidated milestone can fan
out concurrently; sibling milestones can fan out but
each carries the planner / design / verify overhead.
Together they buy back the wall-clock-time gap; alone
each is incremental.

**Sequencing:** deferred until parallel coordination
ships. Shipping consolidation alone gets the cost win
but leaves the clock-time win on the table; shipping
both together is the regime change.

### LDR re-run as T-ab64 validation

The LDR pilot exposed the hollow-verify gap (per the
limitations chapter and substrate-evolution chapter
Phase 4). T-ab64 shipped four new end-to-end verification
checks. The next pilot is the LDR re-run on the
post-T-ab64 substrate.

Outcomes:
- **Clean third receipt**: LDR ships at a comparable
  cost to first run ($15-25 range) with the four
  end-to-end gates passing. Becomes the third working-app
  receipt, strengthens the cost-trajectory claim, AND
  demonstrates T-ab64 closed the hollow-verify gap
  operationally.
- **Surfaces new substrate gap**: re-run still produces
  hollow features in a class T-ab64 doesn't catch.
  Becomes another paper-grade substrate finding +
  the next T-ab task.

Either outcome is paper-grade. The re-run is the
substrate-evolution chapter's most immediate next data
point.

### Existing-codebase / change-request feature surface

The substrate currently bootstraps from a directive + a
skeleton. It doesn't yet support "here's an existing
codebase, implement this change request." Adding this
surface would let the substrate handle the most common
real-world software work shape: iterating on existing
software, not green-field MVPs.

The architectural work:
- **Ingestion**: an existing codebase becomes
  artifact-attributed (every existing file is an
  implementation artifact; every existing dependency a
  contract). The substrate's typed-state model has the
  shape for this; what's missing is the import pipeline.
- **Change-request directive shape**: directives currently
  describe what to build; change-request directives
  describe what to change. The milestone-plan agent would
  need a new mode that treats existing-codebase state
  as the foundation other capabilities build on.
- **Verify substrate adaptation**: end-to-end gates
  (T-ab64 et al.) need to handle the case where some
  existing code is allowed to be untested / placeholder
  / etc., while new code must pass the gates.

**What this would test:** whether the substrate
generalizes from green-field MVPs to the messier shape
of real software work. Paper consequence: positions
Wonderland as a substrate for ongoing software work,
not just a Devin-class one-shot tool.

### Feature sequencing with depends_on (837b5bbb)

Operator observation during mvp: *"putting features in
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

mvp surfaced this: Alice gets confused about persona
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

## §9.3 — Comparative experiments (the rigor expansion)

The evidence chapter is honest about what hasn't been
measured rigorously. Several comparative experiments would
close that loop. Each is cost-bounded and tractable to run
now.

### One-sentence directive pilot (near-term)

The pilots to date have used operator-written directives
(~80 lines each — full specifications covering capabilities,
stack constraints, non-goals, success criteria). The
substrate has not been tested on a genuinely short directive
("build me a markdown notebook" — one sentence, no spec). A
common reader intuition is that working SDLC substrates
should be able to operate from very short prompts and have
the interview / discovery workflow elicit the rest from the
operator. Wonderland has the interview workflow shape
(`discovery.yaml`) to support this, but the path hasn't been
exercised end-to-end at one-sentence-directive scale.

The honest scope-narrowing this implies: the receipts in §7
demonstrate Wonderland operating on
substantially-specified directives, not on one-sentence
prompts. Whether the substrate's discovery workflow can
recover the operator's intent from a one-sentence prompt and
ship comparable working artifacts at comparable cost is an
**open question, not a demonstrated capability.**

The near-term commitment: run a one-sentence-directive pilot
on the same notebook task ("build a personal markdown
notebook web app") and publish the receipt — discovery
artifact length, milestone-plan emission, cost-per-feature
trajectory, shipped-artifact quality against the receipts
the long-directive notebook pilots produce. The operator
expects either (a) the discovery workflow elicits enough
spec from interview that the rest of the pipeline operates
normally, in which case the abstract's directive-size claim
generalizes meaningfully, or (b) the substrate produces
under-spec'd or off-target artifacts because the
discovery workflow doesn't yet do the lift required to
compensate for spec absence — in which case the
short-directive scope becomes an honest published ceiling on
the substrate's autonomy and a load-bearing direction for
discovery workflow improvements. Either outcome publishes.

### Second independent cold review on redux (near-term)

The mvp pilot received an independent cold review at the
shipped-artifact level — operator-commissioned but
read-by-someone-other-than-the-substrate-builder, in the
sense that the reviewer hadn't been involved in the
substrate's design or evolution. That cold reviewer
generated the "competent, above-average code for an MVP"
artifact-quality framing the limitations chapter relies on.

**Redux + LDR have not received the same treatment.** Per
the methodology chapter's bounded-independence
acknowledgment (§5 *"Theseus reviews as structured
falsification"*), the operator's Theseus subagent is
adversarially-framed and schema-disciplined but is not
equivalent to a second-pair-of-eyes review. A near-term
commitment: commission an independent cold review on the
redux shipped artifact, with the same framing the mvp cold
review used (independent reviewer reads the working app
fresh, files findings, grades artifact quality against
their professional reference frame). The outcome publishes
as a follow-up artifact regardless of finding pattern.
Estimated cost: 1-2 hours of an independent reviewer's
time + their reading discipline; no LLM spend.

This is the cheapest near-term move that tightens the
operator-in-loop falsification claim's bounded-independence
gap. The longer-term move (a second-author / external
research-group adoption + replication) is a research-program
question rather than a near-term action.

### Head-to-head measurement on a multi-agent framework (ChatDev on the notebook directive)

The related-work chapter (§10.1) compares Wonderland's
artifact set to ChatDev's *as characterized from ChatDev's
published documentation* — not as measured under matched
conditions. The honest tightening: run ChatDev on
Wonderland's mvp-redux notebook directive, count its actual
artifact output, measure its actual cost, and report the
artifact-density-per-agent-tax-dollar comparison as
measurement rather than characterization. Cost-bounded:
ChatDev's published sub-$1 / sub-7-minute claim sets the
upper bound on what running the comparison would cost.
Estimated effort: ~3-5 hours operator time (environment
setup + run + artifact-set audit) + ~$1-2 LLM spend.

Either outcome publishes. If ChatDev produces 5+ artifact
types at sub-$1 and the artifact-density-per-dollar metric
favors ChatDev on raw count, the related-work paragraph's
qualitative argument (structural richness, citation chains,
cross-pilot accumulation) becomes the only defensible move
and the quantitative-density framing should be retired. If
ChatDev produces meaningfully less than its published claim
suggests on this specific directive, the head-to-head data
strengthens the artifact-density framing meaningfully. The
work is small; the rigor return is high.

### Single-shot Haiku / Sonnet baselines for code quality — PARTIALLY DONE

Status update: the single-shot and Claude Code baselines
have been partially run. The
[comparison-baselines analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/comparison-baselines/README.md)
documents what shipped from each baseline against the same
notebook directive that mvp + redux ran. Findings include
the
[adversarial-review-of-baselines](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/comparison-baselines/adversarial-review-of-baselines.md):
30 blocker-class bugs across 4 single-shot baselines that
ship code without any review pass. Categories match what
Caterpillar catches in the Wonderland pilots.

What's still open from this section:
- **Sonnet single-shot** at full scope — partial coverage
  exists; a clean full-directive run on Sonnet 4.6 would
  close the comparative loop at the model-class boundary.
- **OSS markdown-notebook contrast** — still pending; a
  comparable-scope OSS project for absolute-quality
  comparison.
- **Cross-substrate-version baseline contrast** — would
  re-run a prior-substrate-version pilot on a current model
  to isolate substrate-version from model-version effects.

**What's been confirmed:** single-shot baselines do not
produce working code at the apparent-scope of the directive
— per the operator's mid-investigation correction,
*"Single-shot does not produce working code we found on
closer inspection of our baselines, remember?"* The relevant
competitor class is Devin-shaped agentic systems, not
single-shot inference. Section below.

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
[comparison-baselines analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/comparison-baselines/README.md)
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

**The methodological problem** discussed in §5.X
(comparator-fairness) applies to P7's design too: any
specific "generic prompt" baseline lives on the
strawman-to-convergent spectrum. A version of P7 that
handled the spectrum honestly would pre-register multiple
"generic" conditions at different prompt-detail tiers and
report results across all of them — letting readers
calibrate the spectrum themselves rather than collapsing
it to a single comparison.

### Caterpillar comparator experiment (pre-registered, ready to execute)

A narrow agent-level hygiene check, pre-registered in
Appendix C: a single agent (Caterpillar), single fixed task
(M8 review of a shipped feature with a known cross-cutting
bug), two conditions (full constitution vs literary-register-
stripped operational-rules-only version), six metrics, three
pre-registered hypotheses with interpretation rubric. ~$5-10
LLM spend, ~5-7 hours operator time. **This experiment is
not load-bearing for the unified claim §2 + §5 develop**
(see Appendix C's scope qualification); it is a hygiene
check on one component of one agent's constitution.

The experiment was scoped during this paper's preparation and
**explicitly held out of this paper because executing it would
generate enough material to require its own analysis chapter,
splitting the paper's focus** on substrate evolution and
cost-trajectory findings. The design is ready for execution by
this paper's operator (in a follow-up paper) or by any
researcher who picks it up. Both constitutions are committable
to the repo; the harness is small (the substrate already
supports `load_constitution(name)`); the pre-registered rubric
defeats post-hoc rationalization that would otherwise
contaminate the result.

The pre-registered design + both constitutions ship in the
repository; anyone — including a hostile reviewer — can
execute it. Holding the experiment indefinitely without
execution would itself become evidence against the paper's
claim; the paper's bet is that execution happens and the
result, whatever it is, sharpens rather than collapses the
identity-engineering framing.

This is a *narrow* agent-level hygiene check on one element
(literary register), one agent (Caterpillar), one task
(M8 review), one model class (Haiku 4.5). It does not settle
the unified claim §2 develops — the unified claim's
falsifier is framework-scope (the combined
artifact-density + characteristic-failure-mode-discipline +
cost-trajectory test §2 names), not agent-scope. Appendix C
contributes to identity-engineering hygiene at the
constitution-authoring level; it does not validate or
refute the architectural claim about
identity-as-organizing-principle.

**Why this matters as future work**: handing the reader an
executable pre-registered comparator design — with both
constitutions specified, the fixed task chosen, the rubric
thresholds written before any runs — is itself a research
contribution. Most papers that defer comparator work to
"future work" defer it indefinitely. This paper defers
specifically and tractably: anyone can execute Appendix C
against the current substrate and report results that update
the paper's identity-engineering framing per the pre-registered
rubric.

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

The Haiku-architecturally-optimal hypothesis
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

## §9.4 — Cross-shape transferability

Three of the four completed Tier 2 pilots used variants of
the notebook-class directive (mvp + redux = same directive;
mvp-demo = early partial pilot on similar shape). obol-260522-1
extended the substrate to a CRM project — meaningfully
different scope, but still web-app shaped (fullstack-fastapi-
react skeleton). LDR added dashboard + external-API-integration
shape (auth + multi-card dashboard + 3 external API
integrations + timezone math), still on the same skeleton.

The substrate's properties have been tested on three
sub-shapes of the same broad category (fullstack-fastapi-react
web app: notebook, CRM, dashboard). What still hasn't been
tested:

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

#### Pre-registration: next-pilot directive-shape commitment

To turn directive-shape generalization from "future work"
into a falsifiable next-pilot prediction, the operator
pre-registers: **the first pilot shipped after this paper's
publication snapshot will use a directive class outside
fullstack-fastapi-react** — most likely a CLI tool or a
backend-only service (both have substrate framings ready;
neither has been pilot-tested). The operator commits to
publishing the post-pilot artifact (cost trajectory + scope
+ failure-class surfacing) against the falsifier framing in
§5, regardless of outcome. If the substrate transfers
cleanly, the directive-shape generalization claim gets a
data point. If the substrate requires substantial
adaptation (new agent identities, fundamentally different
workflow shapes), the bounded-to-fullstack-fastapi-react
framing the paper currently maintains becomes the published
ceiling on substrate generality at this iteration of its
life. Either outcome publishes; the pre-registration is the
discipline.

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

## §9.5 — New cast capabilities

### Holmes / Watson workflows (incident response, security audit, codebase backfill)

Per the cast walkthrough (Appendix B): Holmes +
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

## §9.6 — Architectural research questions

The project has accumulated a set of longer-horizon research
questions — substrate self-modification (a forward Tier 3 where
agents propose and ship substrate fixes during pilots rather
than between them), self-hosting (using Wonderland to build the
next version of Wonderland), multi-operator concurrency, the
interviews-and-milestones layer as a long-running collaboration
substrate, identity-engineering instantiations in non-software
domains (medical, academic, engineering casts), and the
methodological work of constructing fair comparator frameworks
for identity-engineering claims (per §5.X). These are
project-internal research notes rather than experiments this
paper proposes for the next 6-12 months; they appear in the
[project memory](`memory/MEMORY.md`) and roadmap and would be
the natural research agenda for whoever picks up identity
engineering as a discipline.

The paper does not develop these further because doing so would
risk converting "this paper opens up future research directions"
into "this paper sketches several research papers it does not
write." Per the editor-reviewed scoping discipline, we name the
directions exist and point at the artifacts that develop them
internally, rather than expanding the paper into a research-
agenda document.

