# Wonderland Cost-Driver Analysis — obol-260522-1

**Status**: pre-pilot prep, post-0.10.0 release
**Pilot under analysis**: obol-260522-1 (24 tdd-implement runs + 23 tdd-design runs across 6 milestones)
**Analysis date**: 2026-05-23
**Originally scoped**: Caterpillar M8 cost investigation. **Extended to**: full design + implement per-meeting cost decomposition + lever ranking by act/pass signal.

## Headline finding

**Tweedles in M8 are the dominant cost driver, not Caterpillar.** Across 29 review threads in obol-260522-1, tweedles spent **$15.60** in M8 vs Caterpillar's **$7.13** — tweedles are **2.2× the M8 cost**. Tweedles pass 80% of their M8 priority windows but pay full per-call cache_creation cost for each one.

The original "Caterpillar M8 dominates implement cost" framing in the investigation premise was wrong — Caterpillar's per-thread cost is moderate ($0.24–0.50/thread); the dominant line is tweedles' silent priority-window overhead in the review meeting.

## What T-ab39 actually accomplished

T-ab39 (`memory_scope: meeting_only` on the review phase) was the most recent attempt to compress Caterpillar's M8 context. The data says it worked:

| Milestone | n calls | median cache_creation | mean | max |
|---|---|---|---|---|
| m1-foundation-data-layer | 98 | 501 | 2,682 | 25,775 |
| m2-kohl-dashboard-entry-point | 207 | 539 | 3,200 | 106,650 |
| m3-kohl-transaction-ledger-and-categorization | 102 | 578 | 2,368 | 25,807 |
| m4-kohl-budget-tracking-and-status | 66 | 769 | 3,033 | 22,851 |
| m5-kohl-debt-paydown-tracking | 42 | 850 | 3,530 | 20,928 |
| m6-csv-and-ofx-import | 34 | 572 | 3,757 | 23,416 |

Median per-call cache_creation tokens stay under 900 across all milestones — well under the 20K+ ceiling we feared. The means are higher because of long-tail cold-cache first-window calls (M2's 106K max is the outlier — a totally fresh cache write). **Caterpillar's review context isn't bloating per call.** T-ab39 is doing its job.

What does drive cost: **call volume**. Caterpillar makes ~19 calls per M8 thread (tool loops — read_file, list_files, git_status, git_diff, verify_imports). Per-call median cost is ~$0.005–0.013, totaling $0.24–0.50/thread.

## The tweedles overhead breakdown

| Agent | M8 calls | M8 cost | avg/call | ACTED windows | PASSED windows | pass rate |
|---|---|---|---|---|---|---|
| caterpillar | 549 | $7.13 | $0.013 | 15 | 15 | 50% |
| tweedledee | 646 | $6.84 | $0.011 | 6 | 24 | 80% |
| tweedledum | 744 | $8.76 | $0.012 | 6 | 24 | 80% |

Two observations:

1. **Tweedles pass 4 out of 5 windows but still make ~22 calls per thread per tweedle.** Each priority window opens deliberation, which involves compose_context + tool loops + final response decision. Passing isn't free — it's a full LLM call cycle that *ends* in "decision: silence." The 22 calls/window/tweedle suggests they're using tools (read_file, grep, run_tests) to evaluate the work before deciding they have nothing to add.

2. **When tweedles DO act, they emit meaningful artifacts.** Across all obol-260522-1 M8 threads, tweedledum emitted 242 `implementation` summaries; tweedledee emitted 220 `contract_note` finalizations + 25 `implementation` summaries. These are real contributions to Caterpillar's review context — "here's what I built, here's the contract I locked in." Not pure noise.

So tweedles are paying full priority-window cost (compose_context + tool exploration + deliberation) for the 80% case where they ultimately decide they have nothing to add to a review they're attending. The 20% case is load-bearing.

## Architectural intent vs reality

The tdd-implement YAML at `closet/workflows/tdd-implement.yaml:640–645` carries a comment that's load-bearing for this analysis:

> Tweedle defense, if relevant, shows up as concerns during the review phase before Caterpillar's verdict lands — the §III selectively-engaging rules let Tweedles buzz in without a standing roster slot.

The design intent was for tweedles to be available-but-not-rostered — opt-in to defense when they notice a misreading, opt-out when the review is going fine. In practice, they're in the roster:

```yaml
- id: review
  roster: [caterpillar, tweedledee, tweedledum]
  phases:
    - name: review
      max_rotations: 2
      team_groupings: [[caterpillar, tweedledee, tweedledum]]  # CONCURRENT
      exit_condition_artifact: review
```

The `team_groupings` is a single team of three, so every rotation opens windows for all three agents concurrently (Two-Headed Giant pattern from analysis 034). The §III "selectively engaging" rule for tweedles applies to in-character speech act decisions, NOT to whether priority windows open — windows open regardless of whether the agent has something to say.

## Levers — ranked by impact / risk

### Lever A — Remove tweedles from M8 roster entirely

**Impact**: Saves ~67% of M8 cost (the ~$15.60 / ($15.60 + $7.13) = 68.6% currently spent on tweedles' priority windows).

**Risk**: Loses the 20% acting case where tweedles emit defense concerns or implementation summaries Caterpillar uses. To preserve continuity:
- Auto-emit a "what I built" summary at end of M7 implementation phase (tweedle-side hook)
- Seed those summaries into M8 review as bus seeds (same shape as existing contract/ticket seeds)
- Caterpillar's review then reads the summary artifact off the bus without paying for tweedles' M8 priority windows

The §III selectively-engaging rule could still apply at the OUTER meeting level — tweedles can buzz in via cross-meeting nudges if they spot a problem, but they don't get standing M8 windows.

**Estimated per-feature M8 savings**: $1.00–$1.20 (i.e., from ~$1.50/feature down to ~$0.50/feature on full-review threads).

### Lever B — Sequential team_groupings (one-at-a-time windows)

**Impact**: Marginal cost reduction (~10–20%). Tweedles still get windows but they see Caterpillar's prior-window output, so the "deliberate then decide to pass" cycle gets cheaper (informed pass faster than uninformed pass).

**Risk**: Lowest — doesn't change roster, just opens windows sequentially.

**Tradeoff vs A**: Smaller savings but preserves the "buzz in if something looks wrong" continuity without adding a new seed mechanism. Good interim move if Lever A feels too aggressive.

### Lever C — `max_rotations: 1` for review phase

**Impact**: Halves the budget for the meeting. Currently 2 rotations × 3-team concurrent = up to 6 windows per phase. With max_rotations: 1, that drops to 3 windows.

**Risk**: Loses the second-rotation case where Caterpillar's first verdict prompts tweedles to defend OR Caterpillar revises after seeing tweedle pushback. Empirically, most M8 phases in obol-260522-1 hit `reason='exit_condition'` after one rotation (Caterpillar ships verdict, phase ends) — so a max_rotations: 1 wouldn't lose much in practice but would still close off the defense pathway.

**Best paired with A or B**.

### Lever D — Per-agent rotation budgets

**Impact**: Asymmetric — caterpillar gets max_rotations: 2, tweedles get max_rotations: 1. Tweedles get one chance to defend then yield.

**Risk**: Substrate work — `PhaseDefinition` currently has one `max_rotations` for the whole phase. Adding per-agent budgets is a substrate primitive change, not a YAML tweak.

**Probably not worth the substrate complexity** unless Lever A and B both prove insufficient.

## Recommendation

Ship **Lever A** for the next pilot. Pair it with **tweedle-side end-of-M7 summary emission** so Caterpillar's review still has the "what got built" context that the M8 tweedle utterances were providing. This is the cleanest separation of concerns:

- M7: implementation. Tweedles build. End of M7: emit a `summary` artifact.
- M8: review. Caterpillar reviews the code + the M7 summary artifact. Tweedles are not in the room; they don't pay for windows.
- Cross-cutting: §III selectively-engaging rule still lets tweedles publish concerns to the bus from outside the meeting if they observe something off — those become natural cross-meeting input rather than guaranteed-window participation.

Estimated impact on next pilot: M8 cost drops from ~$1.00–1.50/feature to ~$0.30–0.50/feature. At 6 milestones × ~3 features each = 18 features, that's $12–$18 saved per pilot. Compounding with prior substrate gains, the per-milestone cost trajectory for the next pilot should be materially flatter than obol-260522-1's.

## Caveats

- Analysis is single-pilot (obol-260522-1). Confirming on a fresh pilot needs n=2.
- Tweedles' contributions (242 implementation summaries + 220 contract_notes across all M8 threads) might have been load-bearing for Caterpillar's review quality. Lever A's tradeoff is that we need to receipt review quality stays high after tweedles leave the room — easiest check: compare adversarial-review findings on Lever-A pilot artifacts vs obol-260522-1 baselines.
- T-ab39 was added mid-pilot; my median-cache_creation numbers may straddle pre/post-fix calls. The per-milestone trend doesn't show a clean step-change, but median values are uniformly small post-fix, which is the validation that matters.

## Data anchors

- Telemetry: `projects/obol-260522-1/.wonderland/telemetry/run-*.json`
- Events: `projects/obol-260522-1/.wonderland/runs/*/events.jsonl`
- Tool calls: `projects/obol-260522-1/.wonderland/tool-calls.jsonl` (9058 entries)
- Workflow: `src/wonderland/closet/workflows/tdd-implement.yaml:366–662` (M8 review meeting)
- Episodic memory: `projects/obol-260522-1/.wonderland/memory/{caterpillar,tweedledum,tweedledee}/episodic.sqlite`

---

# Part 2 — Design phase cost decomposition

After T-ab54 shipped, operator raised: "tweedles are also the primary cost drivers in the design phase with their contract negotiation." Initial per-agent aggregate said otherwise — alice + caterpillar were 51% of design cost, tweedles only 18%. **But that aggregate masked the per-feature scaling property.**

## Per-meeting shape and unit cost

Six meetings make up tdd-design, two shapes:

| Meeting | Shape | $/unit | Unit |
|---|---|---|---|
| architecture (M4) | fixed | $0.668 | per design pass |
| contract-negotiation (M5) | per-feature | $0.396 | per feature |
| composition (M2) | fixed | $0.396 | per design pass |
| scoping (M1) | fixed | $0.098 | per design pass |
| consolidation (M3.5) | per-cluster | $0.097 | per cluster |
| decomposition (M3) | per-feature | $0.025 | per feature |

The per-feature meetings (M3 + M5) parallelize via the pipeline runtime — their wall-clock impact is bounded, but **dollar cost still multiplies by feature count** (each lane pays the same as a sequential lane would). Pipeline parallelism is a wall-clock primitive, not a cost primitive.

## Cost-of-clean-design-pass scaling model

- **Fixed cost per pass** (M1 scoping + M2 composition + M4 architecture): **$1.16**
- **Variable cost per feature** (M3 decomposition + M5 contract-negotiation): **$0.42**

Projecting cost-per-milestone by feature count:

| Feature count | Total | M5 share | M5 % |
|---|---|---|---|
| 1 feature | $1.58 | $0.40 | **25%** |
| 3 features | $2.42 | $1.19 | **49%** |
| 5 features | $3.27 | $1.98 | **61%** |
| 7 features | $4.11 | $2.77 | **67%** |

**Operator's hypothesis confirmed for typical milestone sizes.** Anything bigger than 2 features makes M5 tweedles the dominant design-cost line. obol-260522-1's milestones averaged 3–5 features, so tweedles were ~50–60% of design cost on real milestones. The earlier per-RUN aggregate hid this because half the 23 runs were short reruns that crashed before reaching M5.

## M5 tweedles — different shape from M8

Critical distinction surfaced by the act/pass split in M5 contract-negotiation:

| Agent | M5 ACTED | M5 PASSED | pass rate |
|---|---|---|---|
| alice | 3 | 5 | 62.5% |
| tweedledee | 7 | 1 | **12.5%** |
| tweedledum | 7 | 1 | **12.5%** |

**Tweedles in M5 act 87.5% of windows. Tweedles in M8 acted 20% of windows.** Same agents, completely different engagement pattern. The M5 cost is the cost of *real negotiation work happening* — they're proposing contract notes, refining them, locking versions. Not silence-overhead like M8.

This changes the lever framing completely:
- **M8 lever**: remove tweedles from roster → they were overhead (T-ab54 shipped).
- **M5 lever**: removing tweedles is NOT an option — they're the meeting. The lever has to be either (a) compress how many rotations the negotiation needs, (b) make per-call cost cheaper, or (c) accept that M5 cost is the cost of necessary work.

Same-shape, different-conclusion lesson: act/pass signal is the discriminator. A high-cost meeting where the agent acts most of the time is doing necessary work; same cost with 80% pass is overhead.

## Updated lever ranking (post-M5 act/pass data)

### Lever A — already shipped (T-ab54)
Remove tweedles from M8 review roster. **Estimated savings**: $1.00–$1.20 per implemented feature.

### Lever B — M5 rotation compression (candidate, lower-impact than initial estimate)
Cap M5 max_rotations to 1 (currently unspecified — defaults to 3). Force the negotiation to be one-round: tweedledee proposes contract envelope, tweedledum proposes integration shape, both lock or surface a concern, done. Trade-off: loses the iterative refinement loop where one tweedle's contract gets revised after the other tweedle's pushback. Risk: contract drift between backend and frontend (the failure mode M5 was built to prevent).

**Estimated savings**: ~30% of M5 cost = ~$0.12/feature × 3–5 features = $0.36–$0.60/milestone. Modest.

### Lever C — Cheshire Cat + Queen of Hearts in M4 (investigate before shipping)
M4 architecture is the most expensive *fixed* meeting at $0.668/run. Cat contributes $0.34/run (51%), Queen contributes $0.21/run (31%). Queen's $0.21/run on every design pass — for security ruling on most features — is a lot for what should be a screening pass.

**Open question**: what's Queen's act/pass split in M4? If she acts on most architecture decisions (like tweedles in M5), her cost is justified. If she passes most of them (like tweedles in M8), there's an analog of T-ab54 to ship.

**Estimated potential savings if Queen is M8-shape**: ~$0.20/design pass × 6 milestones = $1.20/pilot. Smaller than M5 lever but a fixed cost cut, so it compounds across all milestones.

### Lever D — M2 composition Caterpillar (parked, smallest)
Caterpillar at $0.19/run in M2 has the same many-cheap-calls pattern as M8 review. At $0.19/run × 23 runs = $4.17 total in this pilot, but per-run it's modest. Same compression idea as M5 (cap rotations) might apply but the absolute savings are small.

## What about M1 stories under caterpillar (foundation milestones)?

obol-260522-1 had no foundation-kind milestones — every milestone was `kind: capability`, so T-ab6's roster filter narrowed M1 to alice solo (100% of M1 cost was alice). No data on caterpillar-led M1.

When the pilot does include foundation milestones:
- Roster narrows to `[caterpillar]` per T-ab6's `foundation → [caterpillar]` map
- Meeting shape unchanged (single-voice scoping)
- Expected cost: similar magnitude to alice's $0.098/run, possibly higher because Caterpillar's deliberation pattern is tool-heavier
- Worth measuring on the next pilot if any foundation milestones land

## Receipt checks needed on next pilot

1. **M8 quality holds** under T-ab54 (Caterpillar-only review). Adversarial-review parity against obol-260522-1 baselines on shipped feature artifacts.
2. **M5 tweedle cost trajectory** — does it scale with feature count as projected? Per-feature numbers from a fresh pilot will tell us.
3. **Queen of Hearts M4 act/pass split** — confirm or rule out the "M8-shape" hypothesis for the Lever C candidate.

## Data anchors

- Telemetry: `projects/obol-260522-1/.wonderland/telemetry/run-*.json`
- Events: `projects/obol-260522-1/.wonderland/runs/*/events.jsonl`
- Tool calls: `projects/obol-260522-1/.wonderland/tool-calls.jsonl` (9058 entries)
- tdd-design workflow: `src/wonderland/closet/workflows/tdd-design.yaml`
- tdd-implement workflow: `src/wonderland/closet/workflows/tdd-implement.yaml`

## Methodology notes for paper write-up

Three lenses needed for cost analysis to land correctly:

1. **Aggregate per-agent** masks where the cost actually lives (overlap of agents across meetings).
2. **Per-meeting per-run** masks per-feature scaling (per_item meetings multiply with feature count; fixed meetings don't).
3. **Per-meeting per-unit** (fixed vs per-feature vs per-cluster) plus the act/pass signal is the lens that surfaces real levers.

The first lens led to a wrong conclusion ("alice + caterpillar are biggest"); the second masked the per-feature scaling; the third revealed tweedles as the dominant design-cost line for typical milestones — AND distinguished M5's "high cost from real work" from M8's "high cost from overhead." Operator-directed lens iteration was the unlock.

---

# Part 3 — M6 + M7 implement-phase decomposition

Operator suspicion: "implementation is still most of our overall cost, and most of that is the tweedles writing code. Maybe streamlined episodic memory?" The data both confirms the cost picture AND falsifies the episodic-memory hypothesis. The lever is somewhere else.

## Per-meeting cost in tdd-implement

Across 24 implement runs, $71.36 total:

| Meeting | threads | cost | % of implement | $/thread |
|---|---|---|---|---|
| **M7 implementation** | 75 | **$37.45** | **52.5%** | $0.499 |
| M8 review | 9 | $20.77 | 29.1% | $2.308 |
| M6 tea-party | 46 | $13.14 | 18.4% | $0.286 |

**M7 implementation is the single biggest line item in the entire pilot** — 52.5% of implement cost and bigger than ANY single design meeting. Confirms the operator's premise.

## Per-agent within M7

| Agent | M7 calls | cost | $/call | cache_creation median | mean |
|---|---|---|---|---|---|
| tweedledum | 2048 | $19.25 | $0.0094 | **412 tokens** | 1,828 |
| tweedledee | 1976 | $18.20 | $0.0092 | **403 tokens** | 1,710 |

Two surprises that re-frame the lever picture:

1. **Per-call cost is tiny** ($0.009). M7 isn't expensive per call — it's expensive in aggregate because of call *volume*.
2. **Median cache_creation is ~400 tokens**, which is basically nothing. This is the load-bearing finding for the operator's question: **episodic memory is NOT the cost driver in M7**. Each implementation call carries minimal context. T-ab25a's `memory_scope: meeting_only` on the implement phase (shipped earlier) already pruned the historical noise; what remains is the actual ticket + contract + most-recent rotation history, which is tiny.

Call volume math: 2048 + 1976 calls / 75 threads ≈ **54 calls per ticket implementation**. That's the green-phase TDD loop — read file, run test, see failure, write file, run test, etc. Each tool invocation is one LLM call. Most of those 54 calls are tool-cycle iteration, not deliberation overhead.

## M7 implement vs validate phase split

M7 implementation meeting has two phases:

```yaml
- name: implement
  max_rotations: 2
  team_groupings: [[tweedledee, tweedledum]]  # concurrent
  exit_condition_artifact: implementation

- name: validate
  max_rotations: 1
  team_groupings: [[tweedledee, tweedledum]]  # concurrent
  exit_condition_artifact: implementation
```

Act/pass split (across 79 phase instances each):

| Phase | Agent | ACTED | PASSED | pass % |
|---|---|---|---|---|
| **implement** | tweedledum | 26 | 39 | **60%** |
| **implement** | tweedledee | 28 | 35 | **56%** |
| **validate** | tweedledum | 7 | 19 | **73%** |
| **validate** | tweedledee | 3 | 25 | **89%** |

**Two distinct over-engagement patterns:**

The **implement phase** has tweedles passing 56–60% of windows. Plausible explanation: per_item_roster_filter narrows to one tweedle per stack_span (frontend → tweedledee only, backend → tweedledum only). On full-stack tickets both are in the cast; on stack-specific tickets the off-stack tweedle still appears in `team_groupings` and burns a window before passing. Worth confirming by splitting per-ticket stack_span.

The **validate phase** has tweedles passing 73–89% of windows — close to M8 review's overhead pattern. Validate is `max_rotations: 1` with `exit_condition_artifact: implementation` (same as implement phase). If implement ships the implementation, validate inherits the artifact and exits immediately — but each tweedle still opens a window and deliberates before passing. Same shape as the M8 tweedle issue T-ab54 just fixed: priority window opens, deliberation runs, decision is "nothing to add."

Estimated validate-phase share of M7 cost: ~30% (2 of the ~6 windows per ticket, before pass-rate weighting). With 73-89% of those windows being silence: ~20-25% of M7 cost is validate-phase overhead = ~$8-9 per pilot.

## M6 tea-party — both agents engaged

Different shape entirely:

| Agent | M6 ACTED | M6 PASSED | pass % | $/call | cache_creation median |
|---|---|---|---|---|---|
| mad_hatter | 42 | 15 | **26%** | $0.014 | 488 |
| alice | 39 | 18 | **32%** | **$0.031** | **12,580** |

mad_hatter is doing the test-writing iteration loop (low pass rate, tiny per-call cost). Alice is engaged too but her per-call cost is 2× higher AND her median cache_creation is 12,580 tokens (vs Hatter's 488). She's bringing the persona context fresh each time she's called. Her 39 acts contribute meaningfully but at a 2× cost premium per call.

Open question: does Alice's persona-grounding add 39 acts × $0.031 = $1.21 of value to M6's testing work, or is M6 a Hatter-led job with Alice as occasional grounding (same shape as T-ab54's tweedle question)?

## Why "streamlined episodic memory" wouldn't help M7

The operator's hypothesis was that episodic memory bloat was driving M7 cost. The data says no:

- M7 implement per-call cache_creation median: 412 tokens (~$0.0005 in cache_write cost)
- M7 implement per-call cache_creation mean: 1,828 tokens (long tail of bigger contexts)
- T-ab25a's `memory_scope: meeting_only` (already shipped) compresses the implement phase memory to "current meeting only," already preventing the multi-iteration accumulation

Compare against M8 pre-T-ab39 which DID have a memory inflation problem (203K-token crashes on mvp-demo-rerun-A). T-ab25a applied the same fix to M7 implement, and it worked: median cache_creation is two orders of magnitude smaller. The episodic-memory lever was pulled already.

Where M7 cost actually lives: **call volume** (~54 LLM calls per ticket × $0.009/call = ~$0.50/ticket). Each tool invocation is one LLM call. Tweedles spend ~50 tool cycles per ticket doing the green-phase TDD loop. That's *the actual work of writing code* — it's mostly irreducible.

## Updated lever ranking (post-M6/M7 analysis)

### Lever E — Remove M7 validate phase
**Impact**: ~20-25% of M7 cost = ~$8-9/pilot. Cheap win.
**Risk**: Low. Validate exists as a safety net when implement budget exhausts before shipping implementation. In practice, tweedles pass 73-89% of validate windows, meaning the safety net is rarely triggering on real concerns. Implement's exit_condition_artifact already covers the common case.
**Mechanism**: Drop the validate phase entirely; rely on implement's exit_condition + M8 review + the M9 substrate-side verify pass to catch issues.

### Lever F — Per-stack-span team_groupings in M7 implement
**Impact**: ~10-15% of M7 cost on stack-specific tickets. Smaller.
**Risk**: Low. Currently `team_groupings: [[tweedledee, tweedledum]]` even though `per_item_roster_filter` narrows the per-ticket cast. If the filter narrowed to a single tweedle, team_groupings should follow — making the meeting truly single-agent for stack-specific tickets.
**Mechanism**: Compute team_groupings dynamically from filtered roster at iteration time, or drop team_groupings entirely (default one-agent-per-team).

### Lever G — Alice in M6 (lower priority)
**Impact**: ~$1.20/pilot if Alice is removable. Same shape question as T-ab54 — does her persona grounding add value to test writing?
**Risk**: Medium. Persona-grounded tests are higher quality (operator memory `project_constraints_improve_quality.md`); removing Alice might reduce test quality. Worth measuring before changing.

### Lever H — Episodic memory streamlining (operator hypothesis — NOT a lever)
**Impact**: Negligible for M7. T-ab25a already prunes implement memory to meeting_only; median cache_creation is 412 tokens, basically free. Further pruning won't move the needle.

The hypothesis was reasonable given M8 pre-T-ab39 had the episodic-bloat problem. It just doesn't apply to M7 anymore — the same fix was already shipped there. The data is the receipt that T-ab25a is doing its job.

## Recommendation for next pilot

Ship **Lever E** (drop M7 validate phase) as T-ab55 if you want a quick win before the pilot. Lever F (per-stack team_groupings) is more invasive — substrate change to dynamically compute team_groupings from filtered roster. Both are pre-pilot candidates; Lever G is a post-pilot measurement question.

**Final cost-driver ranking across the full pilot:**

| Rank | Driver | Pilot $ (approx) | Mitigation |
|---|---|---|---|
| 1 | M7 implementation (green-phase tool loops) | $37 | Mostly irreducible work |
| 2 | M8 review (tweedles + caterpillar) | $21 → ~$7 | T-ab54 shipped |
| 3 | M6 tea-party (red-phase test writing) | $13 | Maybe Lever G |
| 4 | M5 contract negotiation (tweedles) | $4 | Lever B parked |
| 5 | M4 architecture (Cat + Queen) | $4 | Lever C pending data |

The big remaining cost line (M7 at $37) is **the actual cost of writing the code**. Wonderland's substrate makes this happen with Haiku at <$0.50/ticket — a clean signal that the architecture is in the right cost regime. The remaining design + review costs are smaller knobs.

---

# Part 4 — Correction: episodic memory IS most of M7 cached context

Operator caught a misread in Part 3: "412 cache_creation seems really low, wouldn't that mean their constitutions and memory aren't caching at all?" The catch landed — I'd missed the per-call delta vs cached-prefix distinction.

## Cache picture, corrected

Full per-call token breakdown for tweedles in M7 implementation:

| Metric | tweedledum (n=2048) | tweedledee (n=1976) |
|---|---|---|
| cache_read median | **30,345 tokens** | **29,303 tokens** |
| cache_read p90 | 58,077 | 52,318 |
| cache_w median | 412 (per-call delta) | 403 (per-call delta) |
| cold calls (cache_read=0) | 16 (1%) | 17 (1%) |
| warm calls | 2032 (99%) | 1959 (99%) |
| **Total prompt median** | **34,659 tokens** | **33,847 tokens** |

**Caching is working perfectly.** 99% of M7 calls hit warm cache. The 412 token cache_w median I'd previously called "tiny" is the per-call DELTA written to cache (the new tool_result added on this iteration) — not the absence of caching. The real cached prefix is ~30K tokens loaded from cache every call at $0.10/MTok = $0.003/call cache_read cost.

## What's in the 30K cached prefix?

The `wonderland.context_size` WARN log fires when total context exceeds 100K tokens. Nine events across the pilot, sample:

```
context-size agent=tweedledum thread=pipe.<feat>.implementation-<ticket>
  total~=108781
  constitution=8610      (8%)
  relationships=0
  thread_history=99932   (92%)   ← dominant layer
  triggers=124
  engagement_state=115
```

**Thread history (episodic memory) is ~92% of the total prompt on big-context calls.** Constitution is 8K, fixed. Everything else (relationships, triggers, engagement state) is sub-1K.

The 9 WARN events are outliers (>100K context). For the typical M7 call (30K cache_read median), the layer breakdown isn't logged (INFO threshold is 30K but the run logs only captured WARN). Extrapolating from the layer ratios in the outlier sample: typical M7 call has ~8K constitution + ~22K thread_history + ~0.2K other = 30K cached. Memory is roughly 70% of the typical M7 cached prefix.

## Why caching looks "small" per-call

When you look at cache_w in isolation, M7 looks tiny because the same agent is making 50+ calls per ticket within ONE meeting:
- Call 1 (cold): cache_w ~15K (constitution + ticket + contracts + memory base)
- Calls 2-50 (warm): each adds ~400 tokens new (the previous tool_result) + reads 30K cached

The cold cache_w (~15K) matches what we'd expect for the constitution + initial context. Subsequent calls within the meeting reuse that cache. Only 1% of M7 calls are cold — caching is doing its job within the tool-loop.

## So is episodic memory a lever?

**Yes, modestly, and primarily as a reliability lever.**

Cost lever (modest): cutting average thread_history from 22K → 11K (50% reduction) would drop cache_read median from 30K → 19K. Savings: ~$0.001/call × 4000 M7 calls = **~$4-6/pilot**. Real but small.

Reliability lever (more important): the 9 WARN events at 100K-110K are within striking distance of T-ab24b's truncation safety net at 420K chars (~130K tokens). If thread_history grows faster on a harder ticket (more iterations, more retries), we'd cross the truncation threshold and start dropping context — or worse, crash before truncation fires on a workflow path that's not protected. Compressing typical thread_history accumulation gives more headroom before the outlier becomes a crash.

## Where the M7 memory lever could land

T-ab25a already ships `memory_scope: meeting_only` on the implement phase, which strips seed utterances (cross-meeting noise). What remains in thread_history is the within-meeting accumulation:
- Window opens + nudges (T-ab27 already drops nudges)
- Agent acts / passes
- Tool calls + tool results (the big one)

**Tool results are probably the dominant within-meeting accumulator.** Each tool call result (file contents, pytest output, etc.) can be 1-5K tokens, and they get included in subsequent calls via the model's own previous-turn-context. With 50+ tool calls per ticket, that's potentially 50-200K of accumulated tool results in the longest cases.

Candidate lever: **tool result compression in compose_context**. Drop or summarize tool results from earlier rotations when composing context for a new window. The current rotation's tool results stay verbatim; older rotations get a summary line like "[rotation 0 read 4 files, ran tests 2× and saw 3 failures]" instead of the full 20K tokens of file content + traceback. Saves the bulk of within-meeting thread_history growth.

This would be a substrate change to `compose_context` rather than a YAML tweak. Worth proposing as **T-ab56** but holding for next-pilot data — if M7 outlier crashes don't appear in the next pilot (post-T-ab54 cleaner runs), this might not be needed at all.

## Corrections to Lever ranking (vs Part 3)

- **Lever F (per-stack team_groupings)** — REMOVE. Operator confirmed (and data verified): per_item_roster_filter already narrows to single tweedle for stack-specific tickets. Backend tickets: 22/22 single-tweedle. Frontend: 19/19 single-tweedle. Full-stack: 34/34 both. The filter is doing its job.
- **Lever H (episodic memory streamlining)** — UPGRADE from "NOT a lever" to "modest cost lever + meaningful reliability lever." Specifically tool-result compression in thread_history. Park as candidate T-ab56 pending next-pilot outlier data.

## Lesson for the paper

The cache_w vs cache_read distinction is non-obvious in telemetry data. A naive reading of cache_w would suggest "barely any caching happening"; the real interpretation is "lots of caching happening + small per-call deltas." This is the kind of telemetry-reading gotcha that's worth calling out in the methodology section — operator catches like this one are how the team avoids shipping the wrong lever based on the wrong interpretation.

---

# Part 5 — Tool-result accumulation is the actual M7 lever

Part 4's "episodic memory IS most of M7's cached context" was *almost* right but missed where the bulk of the bytes actually lived. Re-investigating:

## What's in the M7 implement thread storage

For the 3 biggest M7 implement threads (1+ MB each):

| Thread | Total | Seed % | Non-seed % |
|---|---|---|---|
| Categorization rules / missing-query-function | 1.44 MB | **100% seed** | 0% (dodo nudges only) |
| Budgeted-amount cents conversion | 1.04 MB | **100% seed** | 0% |
| Inconsistent amount cents conversion | 0.88 MB | **99% seed** | 1% (one concern + one impl) |

**99-100% of M7 thread storage is seeds.** T-ab25a's `memory_scope: meeting_only` filters seeds out of compose_context — so at LLM call time, tweedles see basically NONE of this. The 1+ MB stored is filtered before reaching the model.

So the storage bloat ≠ context bloat. The 30K cache_read median has to be coming from somewhere else.

## The actual culprit: tool-result accumulation within deliberate()

Reading `agent.py:1000-1066` — the deliberation tool loop:

```python
loop_messages = list(messages)
for _ in range(max_tool_iterations):
    result = await self.llm.complete(system=..., messages=loop_messages, tools=...)
    if stop_reason != "tool_use":
        return result.text
    # ... build tool_results list ...
    loop_messages.append({"role": "assistant", "content": assistant_blocks})
    loop_messages.append({"role": "user", "content": tool_results})
```

**Every tool result gets appended to `loop_messages` for the rest of the deliberation.** A single deliberate() session can do 5-15 LLM calls (one per tool-loop turn). By turn 10, the message list contains 9 prior tool_result blocks — each potentially 5-65K bytes.

This is NOT in episodic memory. It's in the LLM client's per-call message list, persisting only within one deliberation. It explains the 30K cache_read median: ~8K constitution + minimal thread_history (post-meeting_only) + accumulating tool result history within the deliberation.

## Tool-result size distribution (tweedles, all phases, pilot total)

| Tool | Count | Median | Mean | p90 |
|---|---|---|---|---|
| read_file | 3,201 | 1,806 bytes | 3,364 | 9,375 |
| grep | 906 | 316 | 7,759 | **35,716** |
| list_files | 1,453 | 496 | 2,164 | 5,707 |
| git_diff | 130 | 3,812 | 12,645 | **65,578** |
| git_status | 194 | 1,102 | 3,307 | 11,899 |
| run_tests | 394 | 33 | 419 | 1,111 |

**Long-tail outliers dominate the storage**: a single grep at p90 returns 35K bytes (~9K tokens); a git_diff at p90 returns 65K bytes (~16K tokens). Each such result lives in the message list across all subsequent calls in the deliberation.

Total tweedle tool-result bytes: **23.5 MB = ~5.9M tokens of tool result lifetime** across the pilot.

## Savings model for tool-result capping

Cap each tool result at N bytes; truncate above with a marker telling the model how to recover the dropped content:

| Cap | Bytes saved | Tokens saved | % reduction |
|---|---|---|---|
| 20K | 4.4 MB | 1.1 M | 18.9% |
| 10K | 8.3 MB | 2.1 M | 35.5% |
| **5K** | **12.3 MB** | **3.1 M** | **52.2%** |
| 3K | 14.8 MB | 3.7 M | 63.1% |
| 2K | 16.6 MB | 4.1 M | 70.7% |

**At 5K cap: 52% of stored tool-result bytes saved.**

Cost model — each cap'd byte saves:
- $1.25/MTok on cache_write (once, when result is first added)
- $0.10/MTok on cache_read for each subsequent LLM call in same deliberation (~5 avg)
- Total: ~$1.85/MTok of saved tool-result tokens

At 5K cap: 3.1M saved tokens × $1.85/MTok = **~$5.70 direct LLM-cost savings per pilot**.

Additional indirect savings:
- Smaller context per call → less model distraction → potentially 10-20% fewer iterations needed
- Could compound to **$10-15 total per pilot**, or 14-27% of M7's $37/pilot cost

## What got shipped (T-ab57)

`agent.py` adds `_maybe_truncate_tool_result(content, tool_name)` called inline in the tool loop:

- Cap: 5,000 chars
- Head-preserve strategy: keep first (cap - 200) chars of the result (most useful info typically front-loaded — grep matches, file content from line 1)
- Append marker: `[truncated N bytes for context budget. If load-bearing, re-run <tool> with narrower scope (e.g. line range, more specific pattern).]`
- Non-string content passes through unchanged (defensive against future structured tool results)

The marker actively educates the model to use narrower tool args on retries. read_file already supports line ranges; grep can accept narrower patterns; list_files can target sub-directories. The cap is a forcing function for targeted tool use rather than dump-everything.

3 regression tests cover small-result-passthrough, oversized truncation + marker shape, and non-string defensive handling.

## What this DOESN'T address (parked for future)

1. **Outer-deliberation history compression** — within ONE deliberation we now cap, but the agent's compose_context still loads constitution + meeting_only-filtered thread_history. T-ab25a handles the cross-meeting noise; the within-meeting non-seed accumulation (~3K from the big-threads samples) is a smaller secondary issue.

2. **The "no episodic memory in M7" experiment** (operator hypothesis) — still worth running on next pilot as an A/B against T-ab57's baseline. If T-ab57 closes most of the cost gap vs single-shot baselines, the no-memory experiment might not move the needle further.

3. **Per-tool smarter truncation** — could be smarter than head-preserve (e.g. grep: keep first 10 matches + total count; git_diff: keep most recent file changes; pytest: keep failure summaries). Worth doing if T-ab57's flat cap proves insufficient.

## Updated lever ranking (final, post-T-ab57)

| Lever | Status | Mechanism | Est savings |
|---|---|---|---|
| **A (T-ab54)** | SHIPPED | Remove tweedles from M8 roster | ~$15/pilot |
| **T-ab57** | SHIPPED | Tool-result cap at 5K chars | ~$5-10/pilot |
| E | parked | Drop M7 validate phase | ~$4-6/pilot |
| G | post-pilot | Alice in M6 measurement | ~$1.20/pilot |
| H (no-memory M7) | post-pilot experiment | Eliminate compose_context for implement | Unknown — possibly 50%+ |

**Combined T-ab54 + T-ab57 estimated impact: $26-32/pilot reduction** on obol-260522-1's $92.64 baseline = **28-35% pilot cost drop.** Best per-pilot cost trajectory we've shipped on the substrate. (Earlier draft used $83 from mvp; obol-260522-1 is the correct baseline since it's the most recent pilot and reflects all prior substrate fixes already accumulated.)

---

# Part 6 — Correction: T-ab57 helps all tool-using agents

Operator catch: "this will apply to *all* tool call usage, not just M7. Pretty sure Hatter does quite a bit of tool calling for instance." Confirmed by the data — T-ab57 is implemented at the agent base class level (agent.py tool loop), so every agent that uses tools benefits.

## Cross-agent tool-result cap savings (5K)

| Agent | Calls | Bytes | Saved | % | Primary tools driving savings |
|---|---|---|---|---|---|
| tweedledum | 3,548 | 12.0 MB | 6.3 MB | 52% | grep (3.0M), read_file (1.9M), list_files (0.7M), git_diff (0.6M) |
| tweedledee | 3,334 | 11.5 MB | 6.0 MB | 52% | grep (2.6M), read_file (2.0M), list_files (0.7M), git_diff (0.6M) |
| **mad_hatter** | 901 | 3.6 MB | 2.1 MB | **59%** | grep (1.4M), read_file (0.4M), list_files (0.4M) |
| **caterpillar** | 1,173 | 4.0 MB | 2.1 MB | **53%** | **git_diff (1.2M)**, read_file (0.4M), grep (0.3M), list_files (0.2M) |
| cheshire_cat | 102 | 0.14 MB | 0.01 MB | 8% | read_file (small) |
| **TOTAL** | **9,058** | **31.3 MB** | **16.5 MB** | **53%** | — |

**Two non-obvious findings** vs the original tweedles-only framing:

1. **Mad Hatter saves proportionally MORE than tweedles** (59% vs 52%). His M6 test-writing pattern skews toward big grep results — he's exploring the codebase to write tests, hitting the long tail more often. The directive "ground tests in the ticket's acceptance criteria" leads to broad searches that produce big results.

2. **Caterpillar's big-tool footprint is git_diff specifically** (1.2 MB savings, 35 of 62 calls oversized). Makes sense — git_diff at p90 is 66K bytes for tweedles, similar for caterpillar. Reviewing implementation = looking at code changes = big diffs. T-ab57 caps these at 5K with marker, model can re-run on specific files if needed.

## Revised savings model

Direct LLM cost (cache_w + ~5× cache_r within deliberations):
- 4.1M tokens saved × $1.85/MTok = **$7.24/pilot direct**

Indirect (less distraction → fewer iterations):
- 1.5-2× amplifier estimated
- **$12-18/pilot total estimated**

Per-meeting impact:
- M6 tea-party (Mad Hatter): ~$1.50 direct
- M7 implementation (tweedles): ~$5 direct
- M8 review (Caterpillar's tools, post-T-ab54 removal of tweedles): ~$1.50 direct

## Updated combined-fix projection

| Fix | Savings | Mechanism |
|---|---|---|
| T-ab54 | ~$15/pilot | Remove tweedles from M8 roster |
| T-ab57 | ~$12-18/pilot | 5K tool-result cap, all tool-using agents |
| **Combined** | **~$26-32/pilot** | **28-35% on obol-260522-1's $92.64** |

That's not "shaving" — that's a structural cost-trajectory improvement. The substrate moves from $92.64/pilot to projected **$61-67/pilot** for an equivalent workload. **Compounded with prior substrate fixes** (mvp → mvp-demo-rerun-A → obol-260522-1 already showed ~35% reduction from earlier optimizations), the cumulative trajectory is roughly $130-150/pilot → $61-67/pilot ≈ 50-55% total cost reduction from the original substrate to post-T-ab57.

The obol-260522-1 baseline is the correct one because the prior 35% had already shipped — every fix here is incremental on top of that. Comparing to single-shot baselines: single-shot wrote a comparable app for $2-3. Substrate at $61-67 is still 20-25× more expensive per app, but it ships test coverage + ADRs + contract notes + per-feature reviews + cross-ticket coherence checks that single-shot doesn't produce. The cost gap is what the multi-agent overhead actually pays for — and the gap is now sized as "5-15× single-shot for substantial quality artifacts" rather than "30×+ for the same."

## Caveat — receipts needed

These are projected savings from telemetry of past runs. Next-pilot validation needs:
1. Per-meeting cost telemetry comparable to obol-260522-1 (per-thread cost ledger)
2. Tool-result truncation event count (could log how often the cap fires per pilot)
3. Quality parity check (adversarial review on shipped feature artifacts)

If projected savings materialize, **0.10.x trajectory is the cleanest cost story we've shipped**. If they fall short, the tool-loop hypothesis needs more investigation (possibly per-tool smarter truncation, or "no episodic memory in M7" experiment).
