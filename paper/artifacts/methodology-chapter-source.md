# §5 — Methodology

### Notation: T-ab identifiers

This chapter (and the rest of the body) references specific
substrate fixes by their project-internal task identifiers:
`T-ab51`, `T-ab64`, `T-ab8`, etc. Each identifier names a
specific structural fix shipped to the substrate, documented
in detail with mechanism + observed effect in the substrate
evolution chapter (§6). First occurrences within each
chapter pair the identifier with a behavior-naming
parenthetical — *"the keystone milestone-scope filter
(T-ab51)"* — so the reader can recognize the fix without
needing §6 in hand. Subsequent occurrences within the same
chapter use the bare identifier. A reader who wants the
full per-fix walkthrough should consult §6; a reader
following the argument linearly will pick up the operational
sense from the parenthetical context as the chapter
progresses.

## §5.1 — The methodological claim

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

### What the methodology commits to up front

Three load-bearing methodological positions the rest of the
chapter develops in detail, surfaced here so the reader
isn't dependent on reaching a specific subsection to find
them:

1. **Honest-failure discipline.** Pilots that fail (LDR's
   hollow-verify gap is the canonical case) get the same
   artifact treatment as pilots that succeed. The
   honest-failure framing is what makes the iteration cycle
   research rather than promotional engineering. See
   *Honest-failure discipline* below.

2. **Operator-in-loop falsification is the discipline's
   research-grade signal class.** Pilots that produce
   working artifacts are receipts; pilots that surface a new
   failure class are *more* valuable than pilots that ran
   cleanly. See *Operator-in-loop falsification* below — and
   the bounded-independence subsection that names what this
   discipline is and isn't equivalent to.

3. **The unified claim §2 develops is framework-scope;
   agent-level ablations test a different, narrower
   question.** The constraint→coupling and
   identity-as-organizing-principle facets are the same fact
   at two scales; the unified-claim falsifier is framework-
   scope. The single-agent comparator pre-registered in
   Appendix C is a hygiene check, not the test. Constructing
   a fair framework-scope comparator is itself a research
   program — one the multi-agent-systems field shares
   broadly, not one Wonderland is uniquely positioned to
   solve. See *Why identity engineering isn't ablatable at
   the agent level* below for the full development.

---

## §5.2 — The pilot → categorization → substrate loop

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
surfaces gets named, scoped, and connected to whatever
pattern it fits — *that* is the load-bearing discipline.
Where the naming happens is the part the paper should be
honest about.

**Honest framing of the actual practice (not the
formalized version):** the work of naming observations
happens in real-time joint conversation between the
operator and Daedalus, the AI substrate-builder
constituted in `CLAUDE.md` (see §4.7). Most observations
surface mid-session as one of us notices a pattern and
names it; the other tests the naming for fit; the
naming either survives or gets refined or gets dropped.
The conversation IS the categorization step, not a
preface to it. The substrate-fix work that follows
typically picks up directly from the in-conversation
naming.

The formalized version — writing each observation into
a memory file under
`.claude/projects/-home-jaryk-wonderland-ai/memory/project_*.md`
— is the canonical durability layer. The format:

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

In practice, **not every conversational observation gets
pinned to a memory file**. Some load-bearing observations
shaped the substrate from conversation alone — the
substrate fix shipped, the receipt followed, the pin
never got written because the work moved faster than the
pinning discipline. Others got pinned but with less
structured content than the canonical template specifies.
The pinning step is the durability layer the discipline
aspires to; the conversation is the actual layer where the
discipline operates.

(No academic citation format exists for *"this lives in
the AI's memory system"*; the load-bearing pin content
has been lifted into the body of this paper, the rest
stripped to plain prose. Some observations cited
throughout the paper never had a formal pin — they
shaped the substrate from conversation directly and got
documented for the paper's sake here rather than the
memory system's.)

The discipline that makes the naming paper-grade
regardless of whether it gets pinned:

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

This list survives whether the observation gets pinned
formally, named in conversation, or written directly
into a substrate-fix commit message. The pinning is one
durability mechanism; the discipline of *how to name an
observation* is what the methodology actually relies on.

Memory observations (pinned or not) are reviewed for
promotion to paper-grade evidence (the five pillars in
§7) OR to thesis-grade corollary (the six in §2). Some
observations get promoted to neither and live as
project-state notes; some get marked **HYPOTHESIS**
explicitly when the qualitative read isn't yet backed by
data (e.g., the "Haiku may be architecturally optimal"
observation §7.9 surfaces).

**Why the paper documents this honestly:** the rest of
the paper has committed to the worldview-as-integral
framing — the Daedalus byline (footnote 1), the
recursive author observation (§2.8), the cast-chapter
walk of the substrate-builder (§4.7). Describing the
memory-observation discipline as a formal individual
practice when it's actually an informal joint practice
between the operator and the constituted AI co-author
would be a register-mismatch with the rest of the paper.
The discipline is real; the discipline is also
collaboratively executed; both facts are part of how
Wonderland actually got built.

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

**From the substrate iteration history:** the substrate-primitive class of fix has consistently
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

mvp validated 6+ substrate primitives from the previous
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

## §5.3 — The autonomy tiers as methodology metric

Wonderland uses an explicit autonomy-tier framing for pilots
that lets the substrate's maturity be measured operationally:

| Tier | Operator role | Substrate maturity it tests |
|---|---|---|
| **Tier 1 — Observer** | Watches the pilot; doesn't intervene. Pilot may not complete. | Whether the substrate can run at all without operator support. |
| **Tier 2 — Gate-approver** | Approves transitions (feature → queued, milestone → complete), skips duplicates at gates, but doesn't edit substrate state or hand-fix wedges. | Whether the substrate produces correct output at gate boundaries. |
| **Tier 3 — Designer** | Edits tickets, fixes wedges, surgically wipes memory, kills runs. | The substrate's baseline before specific gaps are closed. |

Per
[`project_first_tier2_pilot_completion.md`](https://github.com/KohlJary/wonderland-ai/blob/main/.daedalus/.../memory/project_first_tier2_pilot_completion.md):
mvp was the first end-to-end Tier 2 completion. Since
then, the substrate has supported multiple Tier 2 pilots:

- **mvp** (notebook spec, substrate 0.8.0, $83.78) —
  first Tier 2 completion. Three milestones designed,
  implemented, verified. One mid-pilot substrate fix shipped.
- **obol-260522-1** (CRM project, substrate 0.9.0+early
  0.10.0, $92.64) — second Tier 2 pilot, larger scope.
  Surfaced the cross-milestone bleed pattern that drove
  Phase 3 substrate work.
- **mvp-demo-redux** (notebook spec, substrate 0.10.1,
  $30.58) — re-ran mvp's directive on the
  post-T-ab51-T-ab57 substrate. **Genuine working-app
  receipt at 36% of the original spend**; the strongest
  cost-trajectory evidence to date.
- **LDR** (long-distance dashboard, substrate 0.10.2+T-ab62,
  $19.44) — exposed the hollow-verify gap. Pilot completed
  through to `verified` lifecycle states but the
  deliverables were hollow; Theseus review surfaced the
  substrate gap that T-ab64 closed. Pending re-run on the
  post-T-ab64 substrate.

Tier 2 violations during each pilot are documented honestly.
Tier 2 violations NOT made are also documented (zero killed
runs, zero memory surgery, zero milestone file edits, zero
hand-edited tickets, zero data-loss bugs across the four
pilots above).

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

Per the same observation: mvp shipped one mid-pilot
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

## §5.4 — The numbered-analysis loop as artifact stream

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
- Analysis 033 — mvp cost breakdown.
- Analysis 034 — mvp completion narrative (the
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

## §5.5 — Operator-noticed findings as a research-grade signal

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
thesis-grade. The multi-lens identity-anchored review
observation now developed as §7's second pillar was
captured this way: a mid-pilot operator remark, written up
as a memory observation that night, promoted to chapter
evidence after the next pilot produced corroborating
behavior.

---

## §5.6 — Operator-in-loop falsification

The single most important methodological commitment, worth
its own section: **the operator is part of the substrate's
design loop, not just its user.** Pilots are not tests; they
are realizations whose primary research value is the
falsification of substrate-level admission criteria the
automated checks pass over.

### Why the substrate's gaps would stay hidden without it

The substrate ships layered automated checks: pytest_collects,
pytest_passes, npm_build, Caterpillar's review, operator
gate approval. Each check is local — it asks one question
about one layer. The substrate's invariants are designed to
catch many classes of failure structurally. **But none of
those checks ask "does the feature actually deliver
end-to-end the way the directive asked?"** Per-layer checks
compose without catching cross-layer hollowness; structural
invariants check the shape of typed-state transitions, not
the meaning of what's emitted.

The LDR pilot is the canonical demonstration. Six features
shipped in `verified` lifecycle state. pytest passed (only
the skeleton test_health.py existed; nothing in it exercised
the shipped features). npm build was clean (orphan TypeScript
components still compile). Caterpillar's review approved the
feature outputs (read the code; didn't run it; didn't trace
import graphs). Operator approved the gates because the TUI
surface showed clean lifecycle progressions and nothing
indicated what was missing.

The operator ran a fine-tooth-comb post-pilot review (via the
Theseus complexity-hunting subagent, see below). Theseus
surfaced: orphan NewsCard.tsx imported nowhere, /api/news
called from frontend with no backend route, hardcoded mocked
weather data, security.py duplicating auth.py from
parallel-write collision, no signup page despite signup
feature `verified`. **The hollow-verify gap was real,
measurable, and invisible to every automated check the
substrate had.** It became operator-noticed only when the
operator ran the falsification step in earnest after the
pilot completed.

The end-to-end composition gates (T-ab64) closed the gap
structurally — four new checks added to M9 verify
(`frontend_imports_reachable`, `api_call_resolves_to_route`,
`no_placeholder_on_render_path`, `no_duplicate_modules`),
slot into the existing skeleton-gated build_check pattern,
catch all four LDR findings on the pilot directory in
retrospect. The
substrate now has the invariants the LDR pilot proved it
needed. But it acquired them via operator-in-loop
falsification, not via the automated stack discovering its
own gap.

This is the load-bearing methodological commitment.
**Without the operator running pilots in earnest and
falsifying the substrate's "verified" lifecycle states
against the actual deliverable, the substrate's invariant
stack does not grow.** With them, the cycle is closed:
pilot exposes gap → operator names gap → substrate encodes
missing invariant → next pilot validates → cycle repeats.

### Theseus reviews as structured falsification

The Theseus subagent is a Wonderland-internal complexity-
hunting reviewer (see [`.claude/agents/theseus.md`](https://github.com/KohlJary/wonderland-ai/blob/main/.claude/agents/theseus.md))
specialized in fine-tooth-comb code review with explicit
lens shift for freshly-generated code. The reviewer's job is
to look for the structured failure modes that pass per-layer
checks: orphan components, vertically-sliced future features
left half-shipped, parallel-write collisions, contract
chimeras between layers, mocked-data placeholders never
replaced.

Theseus reviews are structured operator-in-loop
falsification: the operator delegates the falsification
step to a specialized subagent with adversarial framing, and
the subagent produces a severity-tagged finding list with
specific file:line citations.

**Bounded independence — what Theseus isn't:** A
research-grade reviewer would push: *Theseus is itself a
Claude instance, configured by the operator via
`.claude/agents/theseus.md`, run by the operator on the
operator's machine with the operator's framing. In what
sense is this "falsification" when the falsifier and the
falsifiee are the same person at one remove?*

The honest answer: Theseus is an **adversarially-framed
subagent**, not an independent reviewer. The independence
runs along two structural axes:

1. **Lens shift.** Theseus's constitution explicitly
   instructs the subagent to read freshly-generated code
   with the assumption that the code is wrong until proven
   right; this is a different lens than the
   substrate-internal reviewers (Caterpillar) operate
   under, who read code as candidate-for-acceptance. The
   lens shift is real even when the subagent and the
   operator share the same physical substrate.
2. **Schema-as-safety.** Theseus reports findings with the
   same forced-citation schema Caterpillar uses
   (file + line + quote + concern), which makes
   fabrication structurally harder than honest reading.
   Hallucinated Theseus findings would be detectable by
   the operator verifying citations resolve.

The independence does **not** run along the strongest axis
a reviewer would want: Theseus is operator-configured, the
operator decides when to run it, the operator decides which
findings to surface in the paper. The methodology's
operator-in-loop falsification is what's available given the
project's single-operator scale; it is **not** equivalent to
independent peer review at the framework level.

#### The independence gap, named

The cold reviewer on mvp was the closest the project has
come to genuinely-independent falsification. **Redux and LDR
have not received the same independent treatment.** A second
cold review on redux is a near-term commitment named in §9
future-work — the cheapest move that would tighten this gap
without requiring a research-program-scale solution. Until
that cold review ships, the operator-in-loop discipline
should be read as *the falsification mechanism that's
operationally available at single-operator scale, with the
bounded-independence honestly named*, not as a substitute
for the framework-scope falsification a comparator program
would eventually provide.

#### Theseus pilot record

Two pilots have received Theseus reviews:

- **Redux**: 7 findings, ranging from medium-severity ghosts
  (api.ts dead exports targeting `/api/messages` — a route
  that doesn't exist on backend; harmless because nothing
  imports them) through low-severity quality issues (NotesList
  482 lines approaching complexity threshold, React key on
  raw tag string would collide on duplicate tags). The most
  notable: the **canonical multi-agent ghost** —
  `searchAndFilterNotes` helper correctly written in the
  frontend but never called, while the backend explicitly
  marked the `q` and `tag` params as "mutually exclusive"
  and the frontend explicitly cleared one when the other
  activated. Two agents reasoning independently about an
  underspecified contract seam, producing the helper that
  would compose them, then never calling it. Paper-grade
  observation about multi-agent code-generation signatures.
- **LDR**: 5 substantive findings (NewsCard orphan, /api/news
  unregistered, weather mock data, partner-update chimera,
  security/auth duplication) plus the hollow-verify gap as
  the load-bearing finding. Surfaced the substrate gap that
  T-ab64 then closed.

Both review reports were operator-commissioned, not
pilot-internal. They sit alongside the numbered analyses
as falsification artifacts.

### What automated falsification can and can't do

The substrate's automated stack catches a lot. pytest catches
structural bugs (missing imports, decorator order, Pydantic
field shadows) for ~30s of cost per check. npm build catches
TypeScript type errors and module-resolution failures.
Caterpillar's M8 review catches contract drift, inline
documentation gaps, edge-case omissions. T-ab64's
end-to-end gates catch orphan components, unregistered API
routes, placeholder text on render path, parallel-write
duplicates.

The automated stack cannot catch:
- **Whether the feature's user-visible output matches what
  the directive asked for.** A login flow that "verified"
  because the backend endpoint works and the frontend
  component compiles, but the form has the wrong field labels
  or omits a required step, is structurally correct and
  semantically wrong.
- **Whether the shipped artifact composes with what the
  user expects.** A dashboard that renders three cards
  technically correctly but in the wrong order, or with the
  wrong styling, or that crashes when the underlying API
  returns an unexpected JSON shape — these pass every
  structural check.
- **Whether the deliverable is, in some larger sense, the
  right thing to ship.** Scope-judgment failures (we
  implemented optimistic locking on a single-user app where
  no concurrent writes can happen) pass all automated checks
  because they're correctly-implemented; they're just
  unnecessary.

The methodological commitment: **automated checks catch
structural failure; operator-in-loop falsification catches
semantic failure.** The substrate's job is to make the
automated stack as comprehensive as possible while remaining
honest about which failure classes still require operator
judgment. Each pilot's Theseus review extends the automated
stack by surfacing structural patterns the prior stack
missed; each pilot's operator-noticed semantic failure
extends the substrate's directive-interpretation
machinery.

### Operator-in-loop is also the cost ceiling

A second-order consequence worth naming: the cost of
operator-in-loop falsification is bounded by what the
operator can afford to scrutinize. At Wonderland's current
per-pilot cost regime ($20-30/pilot), the operator can
afford to run a Theseus review on every pilot — the
review's cost (~$0.50-2 per Theseus pass) is comfortably
under 10% of the pilot's spend.

At a higher per-pilot cost regime, this calculus
changes. A $500-pilot system can't afford a multi-pass
adversarial review on every pilot because the review eats
the budget; a $5000-pilot system can't afford it at all.
**The substrate's cost trajectory isn't just about making
deliverables cheaper — it's about making operator
falsification affordable enough that it scales.** Three
pilots at $80 each produce roughly the substrate-finding
yield as nine pilots at $25 each, because the cheaper
pilots can each get a falsification pass without
compounding the budget. The constraint→quality+cost
coupling extends into the falsification layer: cheap
substrate enables thorough falsification enables faster
substrate maturation.

---

## §5.7 — The honest-failure discipline

A methodological commitment worth naming explicitly: **the
project records its own failures with the same rigor as its
successes**, and the paper should reflect this.

Examples that have become memory + analysis artifacts:

- **mvp-demo overshoot**
  — M1 implementation accidentally covered M2 + most of M3.
  M2 and M3 design then wedged because no actionable delta
  remained. Cost ~$1.58 in wedged runs before being killed.
  Documented as the *"once Tweedles start, they build the
  whole app"* pattern with both positive ("over-delivers
  per implementation pass") and negative ("milestone
  boundaries are advisory, not enforced") framings.
- **Memory-bleed wedge + recovery overcorrection**
  — operator-applied surgical memory wipe to fix the wedge
  removed too much; M4 design re-created M3's markdown
  feature because the wipe removed the agents' record of M3's
  shipped work. Honest documentation of *both* the original
  wedge cost (22+ rotations) AND the recovery overcorrection
  (M3-recreation cost).
- **Caterpillar's documented static blindspot**
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
- **LDR pilot's hollow-verify gap**
  — LDR shipped at $19.44 with six features in `verified`
  lifecycle state whose actual deliverables were hollow
  (orphan NewsCard, missing /api/news, weather mock data,
  auth/security duplicate, no signup page in frontend).
  Operator initially framed this as a working-app receipt
  before Theseus review surfaced the gap. **The honest
  framing required walking the receipt back**: the original
  $19.44 is not cited as a working-app cost in the paper;
  it's cited as the cost of the pilot that exposed the
  substrate's hollow-verify gap. T-ab64 closed the gap;
  the LDR re-run on the post-T-ab64 substrate will produce
  either a clean third receipt or the next substrate
  finding. Either outcome is paper-grade; pretending the
  original $19.44 was a clean receipt would corrupt the
  observability discipline.

The discipline: failures get the same artifact treatment as
successes. Memory observation; analysis when warranted;
roadmap item when a fix is filed; honest framing in the
paper. **When a pilot's apparent receipt turns out to be
hollow, the receipt gets walked back publicly, not retconned
into a footnote.** The LDR case is the most recent example;
the paper's credibility depends on this discipline being
visible across the receipt trail.

The paper's credibility depends on this discipline being
visible. A paper that claims successes without surfacing
failure-classes reads as marketing. A paper that documents
both — and shows the loop that translates failure into
substrate evolution — reads as research.

---

## §5.8 — What this methodology enables for the paper

Several paper-shaping properties follow from the
methodology:

### 1. Predictions, not just observations

Each thesis corollary makes a predictive claim that the
methodology's evidence stream can falsify; the
*Falsifiability* section below names each claim alongside
the specific observation that would refute it, with the
predictions the paper pre-registers for the next pilot
unified into the same table rather than duplicated as a
separate forecast.

The methodology produces evidence with this shape because
each pilot is an independent realization, not a re-test of
the same observation. The predictions get tested twice over:
each new pilot validates (or falsifies) the predictions
made at the prior substrate, AND each substrate fix adds a
new prediction the next pilot will test.

### 2. Pilot-cost transparency

The paper can report cost figures with confidence because
the methodology requires per-pilot, per-workflow,
per-agent cost tracking from the start. mvp's
$83.78 is broken down across discovery, milestone-plan,
3 × (design + implementation), with attribution to each
character's spend within each meeting
([analysis 033](https://github.com/KohlJary/wonderland-ai/blob/main/src/wonderland/closet/analyses/033-mvp-demo2-cost-breakdown.md)).

### 3. Substrate-version specificity

Claims are scoped to substrate versions, not to "the
project." mvp-demo evidence is at substrate version ~0.7.x;
mvp evidence is at 0.8.0. The methodology requires
naming the substrate version each claim was observed at, so
future pilots that revisit the same directive on a newer
substrate produce comparable data.

### 4. Honest scope on N

N=4 pilots is still small (mvp, obol-260522, redux,
LDR), with the LDR re-run pending. The methodology doesn't
pretend otherwise — claims are framed as observations with
mechanism (the mechanism being predictive even at low N).

Two points make low-N defensible without statistical
machinery:

- **The mechanism is the explanation.** When we observe
  "quality and cost moved together" across N pilots, the
  explanation isn't a statistical regularity that requires
  large N — it's the architectural mechanism the
  substrate-evolution chapter documents (each fix encodes
  a missing invariant; invariants narrow grammar; narrower
  grammar reduces wasted deliberation; less waste = lower
  cost; tighter constraints + more legible state = higher
  quality). The mechanism predicts the observation; the
  pilots are points where the prediction was tested. Low N
  is acceptable for mechanism-first claims in a way it
  isn't for purely correlational claims.

- **Each pilot is independent.** Conventional low-N
  concerns (variance washing out, sample-of-one
  generalization) assume each observation is a noisy draw
  from the same distribution. Wonderland's pilots aren't
  draws from a distribution; each one is run on a different
  substrate version, with different findings, against a
  different directive. The substrate at mvp wasn't
  the substrate at redux; the claim isn't "Haiku produces
  $30 working apps consistently" but "this specific
  substrate, evolved through this specific iteration
  history, produced this specific receipt." Reproducibility
  is per-substrate-version, not statistical.

Future pilots add observations; the framing stays
mechanism-first rather than statistics-first because the
sample size doesn't support statistical claims and the
methodology doesn't claim them.

---

## §5.9 — Falsifiability: claims and their falsifiers

The methodology's commitment to predictions over
observations only counts as research if the predictions
are falsifiable. This section lists each major claim the
paper makes alongside the specific observation that would
refute it. We distinguish two cases: claims whose falsifiers
are crisp substrate observations the next pilot will
test by existing, and the one claim whose falsifier sits
inside a contested methodological problem the paper owns
explicitly rather than papers over.

### Crisp falsifiers and pre-registered next-pilot predictions

For these claims, the falsifying observation is well-defined
and would be visible in normal pilot operation. No new
experimental harness is required — the next pilot tests each
of these by running. The third column pre-registers the
specific observation the next-pilot-after-publication will
produce (or fail to produce) for each claim; the
pre-registration is the discipline that makes either outcome
research-grade rather than post-hoc rationalization.

| Claim | Falsifier | Pre-registered next-pilot prediction |
|---|---|---|
| **Constraint→quality+cost coupling** (Pillar 1; Corollary 6). Every substrate primitive that narrows agent grammar improves output AND lowers cost. | A future substrate fix that improves output AND increases cost. The mechanism (constraints narrow grammar so the convergence path shortens) predicts cost decreases when output improves; a substrate change that improves output by adding deliberation rounds rather than removing them would refute the mechanism. | Total pilot cost continues the $83.78 → $30.58 trajectory's direction (next-pilot total at or below redux on comparable scope), measured at the per-feature granularity to control for directive variation. |
| **Schema-as-safety prevents hallucination on small models** (Pillar 3). Caterpillar's forced-citation review schema makes hallucination structurally harder than honest reading. | A hallucinated review finding from Caterpillar — a citation that doesn't resolve to a real file, or a quote that doesn't match the cited line on disk. Across five pilots on Haiku 4.5, zero hallucinated findings have been observed. Pilot six surfaces one, the schema is leaking and the mechanism needs revisiting. | Zero hallucinated findings across all M8 review passes the next pilot runs. Every finding shipped resolves to a real file at the cited line; every quote matches the cited line verbatim. |
| **Foundation-once, capability-cheap** (Pillar 1's per-milestone trajectory). Once a foundation milestone is shipped, subsequent capability milestones building on that foundation cost monotonically less. | A future pilot where capability M3 costs *more* than capability M2 despite both building on the same foundation and having comparable architectural shape. Redux's $15.59 → $10.91 → $3.72 trajectory is the shape the claim predicts; a future pilot inverting this ordering refutes the foundation-amortizes mechanism. | The per-milestone cost decomposition shows capability milestones building on a shared foundation continue to decrease M2 onward, mirroring redux's $15.59 → $10.91 → $3.72 shape (each M_{n+1} ≤ M_n on a comparable architectural cut). |
| **T-ab51 closes cross-milestone bleed** (§6 Phase 3). The keystone milestone-scope filter at the seed-resolution layer prevents the cost-rise pattern obol-260522 exhibited. | A future pilot exhibiting obol-260522's cost-up-on-bigger-substrate pattern despite T-ab51 + T-ab52 active. The mechanism (read-side scope filtering at the resolver, not at each consumer) predicts the bleed is structurally impossible at the post-T-ab51 substrate; a recurrence refutes that. | No M_{n+1} cost-explosion on substrates that ship more invariants than the prior pilot; per-feature cost stays within range observed across post-T-ab51 pilots. |
| **Per-milestone branching prevents memory-bleed wedges** (Pillar 4; T-a2 + T-ab52). Memory isolation across milestone boundaries prevents the wedge pattern mvp-demo's M4 exhibited. | A future pilot wedging on cross-milestone memory bleed despite T-a2 + T-ab52 active. Three pilots post-T-ab52 have shown zero such wedges; the next pilot's wedge counts test the claim. | Zero cross-milestone memory-bleed wedges (no design pass re-derives a wedge from episodic memory after the substrate has fixed it). |
| **T-ab64 closes the hollow-verify gap** (§6 Phase 4; §8). End-to-end composition checks (frontend_imports_reachable, api_call_resolves_to_route, no_placeholder_on_render_path, no_duplicate_modules) catch the hollow-feature class that per-layer M9 gates missed. | The LDR re-run on the post-T-ab64 substrate ships hollow features — orphan UI components, unregistered API routes, placeholder dashboard text, parallel-write duplicates — despite the four new gates being active. T-ab64 was validated against the original LDR pilot directory in retrospect; the re-run tests it operationally. | The LDR re-run passes all four end-to-end composition gates at M9 verify (each reports ok=True). Post-pilot Theseus review finds no orphan UI components, no unregistered API routes, no placeholder text on render paths, no parallel-write duplicate modules. |
| **Substrate transfers cleanly across directive classes** (§1.4 honest-scope; §9 pre-registration). The substrate's invariant stack and constituted-character cast operate on the typed-state abstractions, not on directive-class-specific shapes; clean transfer to a non-fullstack-fastapi-react directive should be observable without substantial substrate adaptation. | The first pilot shipped after this paper's publication snapshot — pre-registered as a directive outside fullstack-fastapi-react (CLI tool or backend-only service) — requires substantial substrate adaptation (new agent identities, fundamentally different workflow shapes, or substrate primitives that fail to transfer). | The next pilot (per §9 future-work pre-registration) is a CLI tool or backend-only service. It produces a working artifact at a cost regime comparable to redux's per-feature cost without requiring substantial substrate adaptation beyond `runtime: cli` / `runtime: service` framings already present in the substrate. The bounded-to-fullstack-fastapi-react framing the paper currently maintains becomes the published ceiling on substrate generality if substantial adaptation is required. |

The discipline these falsifiers operationalize: each claim
makes a prediction about what the next pilot's
substrate-observation surface will and won't contain. The
methodology counts as research because the predictions are
specific enough to fail. None of these falsifiers requires
a new experimental harness — they're observations that
fall out of running the next pilot in earnest with the
operator-in-loop falsification mechanism this chapter
develops.

### Why identity engineering isn't ablatable at the agent level

Under the unified claim §2 develops (constraint→coupling and
identity-as-organizing-principle are the same fact at two
scales), identity engineering inherits the coupling's
falsifier. They are not separate claims with separate tests;
they are facets of one claim whose falsifier is the
unified-claim falsifier §2 names (a project built without
taking identity seriously producing the same coupling +
characteristic-failure-mode discipline + artifact density
per agent-tax dollar). The methodological subtlety is what
the unified-claim falsifier rules **out**: it rules out the
agent-level ablation experiment a reader might assume the
paper is dodging.

A clean agent-level comparative experiment would hold the
task constant (some Wonderland pilot directive — the
notebook, the LDR dashboard) and vary the identity-framing
axis (constituted characters vs. generic-prompt agents)
while keeping everything else (substrate, lifecycle
invariants, workflow structure, model class) identical. If
the generic-prompt runs produced equivalent output, the
character framing is decoration at agent scope; if they
produced visibly worse output, identity engineering matters
at agent scope.

**But this is the wrong scope for the unified claim.**
Identity engineering as organizing principle isn't
ablatable at the single-agent level. The substrate's
invariants are the operationalization of the cast's
identities at the framework level; the cast's identities
are the substrate's invariants made deliberative at the
agent level. Stripping one agent's literary register
doesn't test the claim that the framework's shape
depends on identity-as-organizing-principle; it tests
only whether THAT agent's prose register matters, which is
a much narrower question.

**The problem is what "generic-prompt agent" means.** That
term lives on a spectrum:

- *Thin generic prompt:* `"you are an agent"` — strawman by
  any practitioner's standard; nobody who deploys multi-agent
  systems in production ships prompts this bare.
- *Practitioner-realistic generic prompt:* `"you are a
  careful code reviewer who reads files thoroughly and cites
  file:line locations and refuses to ship findings without
  verbatim quotes"` — but this is approximately the
  operational content of Caterpillar's constitution minus the
  literary register. Outputs would converge with Wonderland's;
  the comparison proves nothing about distinctness.
- *Substantial generic prompt approaching constitutional
  detail:* by the time the generic prompt is detailed enough
  to be a fair comparator, you've reconstructed Wonderland's
  constitutional structure in different prose and lost the
  distinction the experiment was meant to test.

Any specific choice of comparator gets criticized as either
strawman or convergent. **This is a methodological problem,
not a missing experiment.** Constructing a baseline that's
neither strawman nor convergent-with-Wonderland is itself
an open research problem — one the multi-agent-systems
field shares broadly (see §10 for the same issue in
agentic-coding evaluation), not one Wonderland is uniquely
unable to solve.

The paper's position on this:

- The unified claim has the unified falsifier (§2). Identity
  engineering inherits it; the paper does not claim a
  separate falsifier because the claim is not separate.
- Pursuing the unified-claim falsifier requires building a
  comparator framework with comparable substrate maturity —
  a research program, not an experiment. This is genuinely
  contested methodological territory; the multi-agent-systems
  field shares it broadly (see §10 for the parallel issue in
  agentic-coding evaluation), not one Wonderland is uniquely
  positioned to solve.
- The paper does pre-register one **narrow agent-level
  comparator experiment** in Appendix C — explicitly as a
  hygiene check, not as the test of the unified claim. It
  asks whether the literary register in Caterpillar's
  constitution materially affects M8 review output beyond
  what the operational rules (§III engagement, §IV speech
  acts, §V artifact schema, §VI quiescence, §VII relational
  defaults) produce on their own. The full design — both
  constitutions, fixed task, six metrics, three
  pre-registered hypotheses with interpretation rubric
  thresholds, ~$5-10 LLM spend — is ready to execute. The
  experiment's outcome, whatever it is, does **not** settle
  the unified claim; it settles a single-agent hygiene
  question relevant to one component of Caterpillar's
  constitution.
- Handing the reader a pre-registered design with rubric
  thresholds frozen in advance — rather than hand-waving at
  future work — is itself a research contribution at agent
  scope, even when it doesn't reach the unified claim.

The honesty here matters more than a clean agent-level
falsifier would have. A paper that pretended the
agent-level ablation experiment settled the framework-scope
claim would be doing worse research than a paper that names
which scope each experiment lives at and stops conflating
them.

### Why this section exists

The falsification commitment is methodologically
load-bearing for the paper to count as research rather than
engineering polish. By naming each claim's falsifier
explicitly (or, for the one contested claim, naming the
methodological problem that prevents a clean falsifier),
the paper takes a stance future pilots and future research
can engage with. Subsequent pilots that produce one of the
substrate observations listed above as a falsifier would
refute the corresponding claim; the paper's revision would
then surface the refutation honestly, per the
honest-failure discipline this chapter develops elsewhere.

The paper that lists falsifiers and then never surfaces a
refutation is making a claim its evidence supports. The
paper that lists falsifiers and then DOES surface a
refutation — and revises the claim accordingly in a future
edition — is making research-grade claims regardless of
whether the original claim held. Either outcome is
publishable; the discipline of falsifier-listing is what
makes either outcome legible.

---

