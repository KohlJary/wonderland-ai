# Methodology chapter source

> Source material for the paper's Methodology chapter. How
> Wonderland has been developed: pilot-driven substrate work
> with categorization-through-failure as the discipline, the
> numbered-analysis loop as the artifact stream, Tier 1 → Tier 2
> autonomy as the progression metric, and operator-noticed
> findings as a research-grade signal class alongside
> instrumented telemetry.

## The methodological claim

Wonderland is built through **pilot-driven substrate
development with categorization-through-failure**. The system
isn't designed top-down to a spec; it's grown through a
disciplined loop:

```
Pilot → Failure surfaces → Failure categorized as memory observation
                              ↓
            Memory observation drives substrate primitive design
                              ↓
              Substrate primitive shipped (often mid-pilot or before next pilot)
                              ↓
        Next pilot validates the primitive AND surfaces the next failure class
                              ↓
                                 (loop)
```

This is methodologically distinct from two adjacent
approaches:

1. **Top-down design.** Specify the full system, implement
   to spec, test against spec. Wonderland was tried this way
   in early phases (P1-P8); the substrate kept missing
   real-world friction the spec hadn't anticipated.
2. **Reactive bug-fixing.** Run pilots, fix bugs as they
   appear. Doesn't produce architecture; produces patches
   that accumulate without coherent direction.

The categorization-through-failure discipline sits between:
each failure gets *named* (memory observation), *scoped*
(what class of bug is this?), *connected* (does it fit a
pattern with prior failures?), and *fixed at the
architectural level appropriate to its class* (substrate
primitive, constitution change, workflow shape, or — when
correct — explicit "this is a known limit, here's the
workaround").

The artifacts of this discipline:
- **Memory observations** in `.claude/projects/.../memory/`
  — every paper-grade finding gets named here before being
  promoted to architecture.
- **Numbered analyses** in `src/wonderland/closet/analyses/`
  — chronological pilot record, written for future operator
  + paper readers.
- **Roadmap items** in the daedalus roadmap — each substrate
  gap gets a stable GUID; gaps cluster into themes
  ("Caterpillar's epistemic bounds at different layers");
  themed clusters drive multi-pilot work.

---

## The pilot → categorization → substrate loop, walked out

### Step 1 — Run the pilot

A pilot is a real attempt to ship a directive end-to-end
through the substrate. Pilots have:

- A directive (the operator-provided ask: "build a Pomodoro
  timer," "build a personal markdown notebook").
- A budget cap (set in advance; honored or transparently
  exceeded with reasoning).
- An autonomy tier (operator's intended role: Tier 1
  observer / Tier 2 gate-approver / Tier 3 designer).
- A telemetry surface (events recorded; cost tracked per
  agent / per workflow / per meeting).

Pilots aren't tests — they're realizations. Failures are
expected and welcomed; the only failure that's wasteful is
one that doesn't surface a new class.

### Step 2 — Failure surfaces

A pilot rarely runs cleanly. Wedges occur (agents stuck in
loops); cost overruns occur (meetings run past budget); silent
quality issues occur (output looks fine but has subtle bugs
the operator catches later). Each is a candidate failure
signal.

The operator's role during a pilot is *observe + adjudicate*,
not *fix*. When something goes wrong, the discipline is:

1. **Let it run to natural failure**, if cost permits. Killing
   a wedged run early loses information about the natural
   convergence behavior.
2. **Capture the surface details**: which meeting wedged, what
   utterances accumulated, what the agents were arguing about,
   what the cost was at the wedge point, what the operator
   would have intervened with under Tier 3 discipline.
3. **Generalize before fixing**: ask "what class of failure is
   this?" before "what's the patch?"

### Step 3 — Categorize as memory observation

The categorization step is what makes this methodology
different from reactive bug-fixing. Each failure that
surfaces becomes a memory observation file in
`.claude/projects/-home-jaryk-wonderland-ai/memory/project_*.md`.

The observation file structure:

```markdown
---
name: <one-line claim>
description: <one-line summary for the index>
type: project
originSessionId: <session in which it was first observed>
---

<Why this happens — the mechanism>

<Concrete evidence — pilot citations, cost, utterance counts>

<Where this lands in the paper — connection to thesis pillars>

<Anti-claims — what this is NOT>

<How to apply — what changes in substrate design or in how
 we frame the work going forward>
```

The discipline that makes this paper-grade:

- **Named claim** — not "agents are sometimes weird," but
  "Caterpillar's findings are deterministic-on-code, not
  stateful-on-history."
- **Mechanism** — the architectural reason this happens.
- **Concrete pilot evidence** — cost, utterance counts,
  artifact references, not impressions.
- **Connection** — does it fit an existing pillar? Does it
  warrant a new one?
- **Anti-claims** — what would refute this, and what would
  be mistaken inference from it.

Memory observations are reviewed for promotion to
paper-grade evidence (the five pillars in the evidence
chapter source) OR to thesis-grade corollary (the six in the
thesis chapter source). Some observations get promoted to
neither and live as project-state notes; some get marked
**HYPOTHESIS** explicitly when the operator's qualitative
read isn't yet backed by data (e.g.,
`project_haiku_is_architecturally_optimal.md`).

### Step 4 — Substrate primitive (or constitution change)

The categorization tells you what kind of fix is appropriate:

| Failure class | Right-sized fix |
|---|---|
| Agent papering over a structural ambiguity | Substrate constraint that forces them to confront it |
| Agent reaching for a tool inappropriately | Constitution adjustment (often §III engagement rules or §IV speech acts) |
| Workflow shape producing redundant work | Workflow YAML edit (rosters, phases, exit conditions) |
| Cross-meeting bookkeeping bug | Substrate primitive (lifecycle state, registry, snapshot) |
| Missing feedback loop | New coverage check, build_check, or convergence detection |
| Known capability limit on small models | Tool exposure (verify_imports), schema discipline, or scoped operator handoff |

**Per memory observation
[`project_constraints_improve_quality.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_constraints_improve_quality.md):**
the substrate-primitive class of fix has consistently
out-performed the prompt-engineering class. When the
diagnosis is "agent is papering over X," the lasting fix is
substrate-level, not constitution-tweak — the substrate
makes papering-over impossible, where the prompt asks the
agent to please stop papering.

### Step 5 — Next pilot validates + surfaces next class

Each substrate improvement gets validated against the next
pilot. **If the same failure recurs**, the fix was wrong-
shaped or wrong-layer; rethink. **If a different failure
surfaces**, the fix held — and the new failure is the next
loop's input.

Per
[`project_first_tier2_pilot_completion.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_first_tier2_pilot_completion.md),
mvp-demo2 validated 6+ substrate primitives from the previous
loop (memory branching held, coverage exemptions held,
snapshot empty-emission guard held, convergence detection in
place but not triggered, env-class verify routing in place
but not triggered, cross-feature consolidation ran cleanly).
It also surfaced 4 new substrate gaps that became the next
loop's input (b3f440c8 cluster — substrate awareness of
prior-milestone shipped work at different layers).

The cluster recognition is itself a methodological move:
when several new gaps share a theme, the next loop's work
isn't N point-fixes but one structural addition that resolves
the cluster.

---

## The autonomy tiers as a methodology metric

Wonderland uses an explicit autonomy-tier framing for pilots
that lets the substrate's maturity be measured operationally:

| Tier | Operator role | Substrate maturity it tests |
|---|---|---|
| **Tier 1 — Observer** | Watches the pilot; doesn't intervene. Pilot may not complete. | Whether the substrate can run at all without operator support. |
| **Tier 2 — Gate-approver** | Approves transitions (feature → queued, milestone → complete), skips duplicates at gates, but doesn't edit substrate state or hand-fix wedges. | Whether the substrate produces correct output at gate boundaries. |
| **Tier 3 — Designer** | Edits tickets, fixes wedges, surgically wipes memory, kills runs. | The substrate's baseline before specific gaps are closed. |

Per
[`project_first_tier2_pilot_completion.md`](../../.daedalus/.../memory/project_first_tier2_pilot_completion.md):
mvp-demo2 is the first end-to-end Tier 2 completion. Tier 2
violations during the pilot are documented honestly (one
mid-pilot substrate fix shipped; this counts as a Tier 2
violation). Tier 2 violations NOT made are also documented
(zero killed runs, zero memory surgery, zero milestone file
edits, zero hand-edited tickets, zero data-loss bugs).

The metric isn't binary "did the operator intervene?" — it's
**at what level did intervention happen, and what gap does
each intervention surface?** Operator skipping a duplicate
feature at a gate-approval point is Tier 2 discipline (queue
decisions ARE gate-approver work). Operator manually editing
the duplicate's ticket file would be Tier 3 (substrate
state edit). The distinction is methodologically
load-bearing: it lets the paper say "Wonderland achieves
Tier 2 autonomy on this directive class at this substrate
version" without dressing up "operator never touched
anything" as the claim.

### Mid-pilot substrate fixes: violations with intent

Per the same observation: mvp-demo2 shipped one mid-pilot
substrate fix (auto-directive synthesis + seed-fallback
milestone-scoping). This **is** a Tier 2 violation —
substrate code shipped during the pilot rather than between
pilots. Documenting it honestly is the methodological move.
It's evidence of iterative substrate maturity: the gap was
surfaced, named, and addressed within the pilot's cost
budget, then validated against the rest of the pilot's runs.

The alternative — pretending the pilot ran on the
substrate version that started it — would corrupt the
observability discipline that makes pilots paper-grade
evidence in the first place.

---

## The numbered-analysis loop as artifact stream

`src/wonderland/closet/analyses/` contains numbered
chronological analyses, one per significant pilot event or
substrate iteration. The current count is ~40+ analyses
across the project's iteration history.

Each analysis is written for two audiences:

1. **Future operator** — picks up where the previous session
   left off, needs to know what was tried, what worked, what
   wedged, what got shipped.
2. **Paper reader** — needs specific pilot evidence with
   cost / artifact / utterance citations.

The analyses are NOT operator-facing UX (those live in the
TUI dashboard); they're research artifacts. The numbered
sequence lets the paper cite specific analyses for specific
claims:

- Analysis 004 — silence-as-settlement on the /health
  directive (Corollary 2 evidence).
- Analysis 027 — Tweedles recovering missing artifacts via
  disk channel (Corollary 3 evidence).
- Analysis 033 — mvp-demo2 cost breakdown.
- Analysis 034 — mvp-demo2 completion narrative (the
  Wright Brothers moment).
- Analysis 040 — order rationale for tdd-design (M1
  features-before-tickets, architecture-after-tickets).

The discipline of analysis-writing also serves as a
**categorization-forcing function**: writing an analysis
forces the operator (and the agent helping) to name what
happened, why, and what changes. Analyses that can't be
written cleanly usually indicate the pilot's outcome wasn't
yet understood; that's a signal to dig further before
shipping the next change.

---

## Operator-noticed findings as a research-grade signal

Per memory observation
[`project_multi_lens_review_produces_quality_code.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_multi_lens_review_produces_quality_code.md):
the operator observed unsolicited mid-pilot that *"we're not
just shipping code, it's quality code. They're accounting for
all types of shit I never would have thought to through the
review passes."* This observation became paper-grade evidence
for Evidence Pillar 2.

The methodological move worth naming: **operator-noticed
findings count as evidence**, distinct from instrumented
telemetry but high-signal because the operator wasn't looking
for the property when they observed it.

Why this matters:

- **Qualitative ≠ low-quality.** An experienced operator
  noticing a property unprompted is a different epistemic
  shape than that operator looking-for-and-finding the
  property. The former is closer to a natural observation;
  the latter risks confirmation bias.
- **Quantitative may not be available.** Some claims about
  the substrate's output ("code quality" as a holistic
  property) don't have clean metrics. Building a metric to
  proxy them creates its own bias (we'd optimize for the
  metric rather than the property).
- **The methodology has a place for both.** Telemetry
  numbers (cost, rotation counts, utterance counts) live
  alongside operator observations in memory files. Each is
  load-bearing for different kinds of claims.

The discipline: when the operator notices a property
unsolicited, capture it the same way as a wedge surfaces —
name it, categorize it, ask what mechanism produces it, ask
whether it's promotable to evidence-grade or
thesis-grade. The
[`project_multi_lens_review_produces_quality_code.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_multi_lens_review_produces_quality_code.md)
memory was created this way; it's now Pillar 2 in the
evidence chapter.

---

## The honest-failure discipline

A methodological commitment worth naming explicitly: **the
project records its own failures with the same rigor as its
successes**, and the paper should reflect this.

Examples that have become memory + analysis artifacts:

- **mvp-demo overshoot** (analysis + memory
  [`project_mvp_demo_m1_m2_overlap.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_mvp_demo_m1_m2_overlap.md))
  — M1 implementation accidentally covered M2 + most of M3.
  M2 and M3 design then wedged because no actionable delta
  remained. Cost ~$1.58 in wedged runs before being killed.
  Documented as the *"once Tweedles start, they build the
  whole app"* pattern with both positive ("over-delivers
  per implementation pass") and negative ("milestone
  boundaries are advisory, not enforced") framings.
- **Memory-bleed wedge + recovery overcorrection**
  ([`project_substrate_fixes_dont_propagate_through_memory.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_substrate_fixes_dont_propagate_through_memory.md))
  — operator-applied surgical memory wipe to fix the wedge
  removed too much; M4 design re-created M3's markdown
  feature because the wipe removed the agents' record of M3's
  shipped work. Honest documentation of *both* the original
  wedge cost (22+ rotations) AND the recovery overcorrection
  (M3-recreation cost).
- **Caterpillar's documented static blindspot**
  ([`project_caterpillar_static_blindspot.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_caterpillar_static_blindspot.md))
  — M8 reliably misses single-file static-time bugs
  (Pydantic field shadows, unresolved forwards, decorator
  order traps). Named as a scope gap, not a Caterpillar
  shortcoming. Fix is a `verify_imports` tool (mechanical
  check for mechanical bugs), not a constitution change.
- **B1 + C2 from the code-quality artifact** — the cold
  reviewer found a blocker (silent If-Match bypass) and a
  concerning bug (revision_id serialization mismatch).
  Documented honestly in the code-quality artifact §6 with
  scope-honest framing (latent at v1, would be acute at v2).

The discipline: failures get the same artifact treatment as
successes. Memory observation; analysis when warranted;
roadmap item when a fix is filed; honest framing in the
paper.

The paper's credibility depends on this discipline being
visible. A paper that claims successes without surfacing
failure-classes reads as marketing. A paper that documents
both — and shows the loop that translates failure into
substrate evolution — reads as research.

---

## What this methodology enables for the paper

Several paper-shaping properties follow from the
methodology:

### 1. Predictions, not just observations

Each thesis corollary makes a predictive claim that the
methodology's evidence stream can falsify. The paper's
strongest move is to frame claims as predictions the
methodology continues to test:

- "Quality and cost will continue to move together in
  Wonderland substrate iterations" — falsifier: a future
  substrate change that improves output but increases cost.
- "Caterpillar's findings will continue to be grounded on
  Haiku" — falsifier: a hallucinated finding in a future
  review pass.
- "Branching memory will continue to prevent cross-milestone
  bleed" — falsifier: a future pilot that wedges on
  memory bleed despite branching.

The methodology produces evidence with this shape because
each pilot is an independent realization, not a re-test of
the same observation.

### 2. Pilot-cost transparency

The paper can report cost figures with confidence because
the methodology requires per-pilot, per-workflow,
per-agent cost tracking from the start. mvp-demo2's
$83.78 is broken down across discovery, milestone-plan,
3 × (design + implementation), with attribution to each
character's spend within each meeting
([analysis 033](../../src/wonderland/closet/analyses/033-mvp-demo2-cost-breakdown.md)).

### 3. Substrate-version specificity

Claims are scoped to substrate versions, not to "the
project." mvp-demo evidence is at substrate version ~0.7.x;
mvp-demo2 evidence is at 0.8.0. The methodology requires
naming the substrate version each claim was observed at, so
future pilots that revisit the same directive on a newer
substrate produce comparable data.

### 4. Honest scope on N

N=2 pilots is small. The methodology doesn't pretend
otherwise — claims are framed as observations with
mechanism (the mechanism being predictive even at low N).
Future pilots add observations; the framing stays
mechanism-first rather than statistics-first because the
sample size doesn't support statistical claims.

---

## Where this lands in the paper

This chapter belongs after the Architecture chapter
(workflow walkthrough material) + Cast chapter (cast
walkthrough material) and before the Evidence chapter.
Sequence:

1. **Thesis** — the architectural claim + six corollaries.
2. **Architecture** — workflow walkthrough material; how
   the system runs.
3. **Cast** — cast walkthrough material; the characters
   whose multi-lens review is the mechanism.
4. **Methodology** — this chapter. The discipline through
   which the system was built.
5. **Evidence** — five pillars validating the corollaries.
6. **Wright Brothers moment** — mvp-demo2 narrative.
7. **Economics** — cost breakdown.
8. **Limitations** — what's still open (the limitations
   chapter source).
9. **Future work** — what the next pilot loops will test.

Methodology before Evidence is the right ordering because
the Methodology chapter explains *how the evidence was
generated*. Readers who don't understand the pilot →
categorization → substrate loop won't read the Evidence
chapter's claims at the right epistemic register.

The Methodology chapter is also where the
**categorization-through-failure** framing lives —
naming the discipline explicitly is what differentiates
Wonderland's development from "we tried things and these
worked."

---

## See also

- [Evidence chapter source](./evidence-chapter-source.md) —
  the artifacts this methodology produced as paper-grade
  observations.
- [Thesis chapter source](./thesis-chapter-source.md) —
  the architectural claims the evidence validates.
- [Code quality artifact](./code-quality-mvp-demo2.md) —
  honest-failure discipline in artifact form (the reviewer
  found bugs; we surface them honestly).
- Memory observation index:
  `.claude/projects/-home-jaryk-wonderland-ai/memory/MEMORY.md`
  — the live record of paper-grade observations as they're
  named.
- Numbered analyses:
  `src/wonderland/closet/analyses/` — the chronological
  pilot record (~40+ entries).
- Roadmap (gaps + clusters):
  `.daedalus/roadmap/` — substrate-evolution work driven by
  pilot failure categorization.
