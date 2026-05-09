# Analysis 032 — TDD-serial v3: first end-to-end completion, and the cost story isn't what we thought

**Date:** 2026-05-08
**Run:** Pomodoro tdd-serial v3 (completed end-to-end at $4.7236 / $5.00 cap, ~28 min wall-clock).
**Snapshot:** [analyses/data/032-tdd-serial-v3/](data/032-tdd-serial-v3/).
**Result:** **First end-to-end tdd-serial completion. M1 → M6 ran clean. 1080 LOC of production code shipped, 10 test files written, Caterpillar reviewed in M6, Tweedles fixed two load-bearing bugs. The per-agent telemetry reframes the entire cost story: Hatter sprawl is *not* the dominant cost driver — Tweedles' M5 + M6 work is. Analysis 031's framing was wrong on this point.**

## What we tested

After analysis 031's tdd-serial v1 + v2 follow-up, the directive shipped two refinements ([commit 6c8ad0f](../../../commit/6c8ad0f) for tdd-serial, [a7d8e76](../../../commit/a7d8e76) for tdd):

1. **Tweedles bounded to ONE concern per iteration in M4**, reactive-not-proactive.
2. **No `write_file` calls at all by Tweedles in M4** — neither production code nor test files.

The bet: v2's "more expensive than v1" outcome was driven by Tweedles getting busier under the v2 positive-work-product framing (test-clarification → write tests + raise concerns + propose contract revisions). Cap their volume on the bus side; see if that compresses cost.

Same Pomodoro directive as v1, v2, and analysis 029 v6 banner: *"Build a Pomodoro timer app: focus sessions, configurable breaks, daily review, persistent settings."*

## Per-meeting + per-iteration cost

| Meeting | Iteration | Cost | Calls | Time | Outcome |
|---|---|---|---|---|---|
| M1 (Caucus Race) | — | $0.0328 | 2 | 20.4s | COMPLETE |
| M2 (Rabbit's Errand) | — | $0.0442 | 5 | 16.2s | COMPLETE |
| M2.5 (Caterpillar) | — | $0.0491 | 8 | 26.0s | COMPLETE |
| M3 (Tweedles) | — | $0.1955 | 19 | 72.3s | COMPLETE |
| **M4 (Tea Party)** | 1 — Focus session | $0.5469 | 54 | 199.7s | MEETING_BUDGET |
| M4 | 2 — Break timer w/ config | $0.6140 | 58 | 165.3s | MEETING_BUDGET |
| M4 | 3 — Daily review | $0.5707 | 50 | 300.1s | MEETING_BUDGET |
| **M5 (Implementation)** | 1 — Focus session | $0.3475 | 48 | 54.7s | **COMPLETE** ✓ |
| M5 | 2 — Break timer w/ config | $0.5875 | 65 | 105.4s | MEETING_BUDGET |
| M5 | 3 — Daily review | $0.5346 | 57 | 96.5s | MEETING_BUDGET |
| **M6 (Trial)** | — | $1.2007 | 99 | 201.3s | MEETING_BUDGET |
| **Total** | | **$4.7236** | **465** | **~28 min** | end-to-end COMPLETE |

Per-iteration M4 average: $0.577 / 54 calls. Per-iteration M5 average: $0.490 / 56 calls.

## Per-agent telemetry — the result that reframes the cost story

| Agent | Calls | Cost | % of total |
|---|---|---|---|
| **tweedledum** | 179 | **$1.821** | **38.6%** |
| **tweedledee** | 179 | **$1.575** | **33.3%** |
| mad_hatter | 65 | $0.901 | 19.1% |
| caterpillar | 27 | $0.326 | 6.9% |
| alice | 9 | $0.040 | 0.9% |
| white_rabbit | 2 | $0.026 | 0.6% |
| cheshire_cat | 3 | $0.019 | 0.4% |
| queen_of_hearts | 1 | $0.017 | 0.3% |

**Tweedles combined = 71.9% of total cost.** Hatter = 19.1%. The "Hatter sprawl is the cost driver" framing analysis 031 led with isn't right. Hatter's per-call cost is normal Haiku territory ($0.014/call); Tweedles' per-call costs are also normal ($0.009-$0.010/call). The volume difference is what dominates.

**Where do Tweedle calls go?** Looking at the breakdown by meeting:

- M3 (contract negotiation): 19 calls combined — the design work
- M4 (3 iterations, both Tweedles in roster): some clarifying questions + (despite the directive bound) some test file writes that landed via tool calls without bus emissions
- M5 (3 iterations, Tweedle-only roster): the bulk — implementation work, `write_file` calls, `run_tests` cycles, iteration on red→green
- M6 (Trial, both Tweedles in roster): Tweedles fixed two load-bearing bugs Caterpillar surfaced, plus answered review findings

Each `write_file` call sends the *full file content* as input tokens. Tweedles writing a 250-line `sessions.py`, then iterating on it via `run_tests` + `write_file` 3-4 more times to fix red tests, produces ~250 + ~280 + ~310 + ~340 = ~1180 lines of input across 4 calls — vs ~250 + ~30 + ~30 + ~30 = ~340 lines if a diff-based tool let them send only the deltas. Roughly **3.5× cost compression** would be available with the right tool. Filed as [roadmap 0858a936](../.daedalus/roadmap/items/0858a936) during this run.

## Comparison vs prior runs on the same directive

| Run | Workflow | Outcome | Total cost | Wall-clock | Code shipped |
|---|---|---|---|---|---|
| Analysis 029 v6 banner | tdd (parallel) | end-to-end | **$3.56** | ~9 min | ~1200 LOC |
| Analysis 031 v1 | tdd-serial v1 | killed @ M5 iter 1 | $4.01 | ~24 min | 1168 LOC |
| Analysis 031 v2 | tdd-serial v2 | killed @ M4 iter 2 | ~$1.74 | ~12 min | partial (M4 only) |
| **This run (v3)** | tdd-serial v3 | **end-to-end COMPLETE** | **$4.72** | ~28 min | **1080 LOC + reviews + bugfixes** |

v3 vs v6 banner: **+32% cost, +210% wall-clock, comparable code volume, plus a deferred-test backlog of 41 scenarios across 10 test files**. The serial workflow pays a real tax in cost and time; in exchange you get per-feature artifact coherence (analysis 031 F2) and a structured deferred-test surface.

v3 vs v1: cost is +18% but completed end-to-end (v1 killed before M5 iter 2). v1's projected end-to-end would have been ~$7-8 had it completed; v3 is ~40% cheaper than that projection thanks to the M4 directive bound.

v3 vs v2: -19% per-iteration M4 cost. The Tweedle bound earned its keep on the bus side — same per-iteration call count, lower cost per call, no more Tweedle proactive-tweet sprawl.

## Findings

### F1 — The directive bound on Tweedles in M4 worked at the bus layer

v3's M4 average iteration cost was **$0.577**, below v1's $0.609 average (-5%) and v2's $0.708 average (-19%). The "one concern per iteration, reactive not proactive" framing kept Tweedle bus utterances down — Tweedledee shipped exactly one concern per iteration ("Contract surface mismatch in test files — blocking M5"), exactly as the bound prescribed.

This is the cleanest signal yet that surface-shaped directive bounds work. Tweedles read the new directive, internalized it, complied. Where the bound *didn't* fully take is the tool-call layer (next finding).

### F2 — The "no write_file at all" rule was bypassed by tool-call invisibility

The v3 directive said "Do NOT call `write_file` in this thread — at all. No production code, AND no test files." Tweedles obeyed on the bus side — no proactive `implementation` artifacts shipped during M4 — but at least one Tweedle tool-called `write_file` for `tests/test_focus_session_with_visual_countdown.py` during M4 iter 1. Detected only because a late-publish surfaced as `[bus record coerced to implementation: write_file calls landed for tests/test_focus_session_with_visual_countdown.py]`.

The directive can constrain what Tweedles *say* (bus side, validated through speech-act emission) but not what they *do* (tool side, not yet surfaced as bus events). Until tool calls are first-class events, tool-shaped directive bounds remain unenforceable through observation. Filed as [roadmap 33e29f5c](../.daedalus/roadmap/items/33e29f5c) at P1.

The structural fix isn't a tighter directive; it's making tool calls visible so the framework can detect the violation in real time.

### F3 — The Hatter-sprawl-is-cost-driver framing was wrong

Analysis 031 led with "Hatter's §VIII sprawl is the dominant cost driver." The v3 per-agent telemetry shows that's false: Tweedles combined are **3.5× more expensive than Hatter**. Hatter's contribution is real but secondary.

What v1 actually showed (visible only in retrospect with v3's per-agent data):
- v1 ran 5 M4 iterations + 1 M5 iter = 6 per_item iterations. Tweedles were in roster for all 6 (M4 has all four, M5 is Tweedle-only).
- Each M5 iteration burns 50-60 Tweedle calls re-shipping growing files via `write_file`. With 5 features × 3 iterations of red→green = ~15 iterations of file-rewrites per Tweedle, the input-token cost compounds dramatically.
- Hatter only ships in M4 (4 iterations × ~7 scenarios × probably 1-2 calls each = ~30-50 calls). His total cost in v3 was $0.90 for 65 calls — modest.

The framing error matters because it pointed toward the wrong fix. Tightening Hatter's directive (which v3 did via the surface-relative + self-audit clauses from analysis 031 F3) was at most a small contributor. The big lever is **reducing Tweedle re-write cost via diff-based tools** ([roadmap 0858a936](../.daedalus/roadmap/items/0858a936)). Compresses input tokens 3-4× on iterative authoring — exactly what Tweedles do throughout M5 and M6.

### F4 — M5 iteration 1 completed naturally at $0.35 — first tdd-serial M5 to settle

In v1, every M5 iteration hit MEETING_BUDGET. In v3, M5 iter 1 (Focus session with visual countdown) settled COMPLETE at $0.3475 in 54.7s — half v1's M5 iter 1 cost.

What's different: with the M4 directive bound, the M3 contract notes were sharper (Tweedles negotiated 7 contract notes against 3 features, vs. v1's 5 against 5), and Tweedles entered M5 with less ambient confusion. The Focus Session feature had clean contracts → straightforward implementation → tests went green quickly → quiescence fired naturally rather than budget-cap firing.

iter 2 and iter 3 both hit budget cap (no iter completed naturally), but at $0.59 and $0.53 they're notably under v1's $0.70 baseline. The compression compounds across the M5 phase: total M5 cost in v3 = $1.47 for 3 iterations vs v1's $0.70 for 1 iteration (projected $3.50 for 5 iterations had v1 completed).

### F5 — M6 ran a full review-and-fix loop for the first time in any tdd-serial

Caterpillar shipped 1 `review` artifact ([review-001-focus-session-and-break-timer-implementation-m6-bugfix-review.md](data/032-tdd-serial-v3/wonderland-snapshot/reviews/review-001-focus-session-and-break-timer-implementation-m6-bugfix-review.md)) across 27 calls. Tweedles responded by shipping 2 implementation artifacts:
- `implementation-001-fix-typescript-type-error-in-focustimer-component.md`
- `implementation-002-fix-focus-session-status-not-updated-to-completed-after-logging.md`

The second is a load-bearing logic bug — focus sessions weren't transitioning to COMPLETED state after their completion event was logged, breaking the daily review feature's data dependency. Caterpillar caught it; Tweedles fixed it. M6 worked exactly as designed: surfaced bugs that the per-feature M5 iterations couldn't see (because each iteration only saw its own feature in scope).

This is the load-bearing M6 work — cross-feature consistency surfacing. The serial workflow's biggest weakness (per-feature M5 iterations don't see each other) is exactly what M6 is supposed to compensate for, and v3 proved the compensation works.

M6 cost was $1.20 (under cap-but-close) for 99 calls. Most of that is Tweedles fix-and-respond cycles (`write_file` + `run_tests` + respond to next finding).

### F6 — Substrate divergence (bus accounting vs disk reality) is still present and routine

Two M4 iterations + one M5 iteration in v3 shipped 0 test_scenario / story / implementation artifacts on the bus, but disk had real test files / implementation written via `write_file` tool calls. Detected only via late-publish messages of the form `[bus record coerced to implementation: write_file calls landed for X.py]`.

This is the same pattern analysis 031 F6 identified — the framework's bus capture undercounts actual work whenever a parse-error empty + late-publish fires. Filed at P1 ([roadmap 92cec468](../.daedalus/roadmap/items/92cec468)). Compounds with the tool-call surfacing item ([33e29f5c](../.daedalus/roadmap/items/33e29f5c)) — both reach into the substrate to make what *actually happened* visible to downstream consumers (analyses, telemetry, the eventual TUI live-watch).

### F7 — Empty-response parse errors still recur at high rates

Six empty-response parse errors during v3 (across 11 thread-iterations: 0 in M1-M3, 1 in M4 iter 2, 4 in M5 iters 1-3, 1 in M6). 50%+ of M5/M6 iterations hit an empty response at some point. Most recovered via parse-retry; one (Tweedledum in M6) hit `deliberate() raised TweedleResponseParseError` after retries failed.

[Roadmap 884bbad2](../.daedalus/roadmap/items/884bbad2) tracks the investigation — the cumulative-context hypothesis remains the leading suspect.

### F8 — The right next bound is on Tweedle iterative-write costs, not on Hatter

Per F3, the diff-based-write-tool roadmap ([0858a936](../.daedalus/roadmap/items/0858a936)) is the leading candidate for the next material cost compression. Implementation:

- Tweedles in M5 iterate red→green by writing → testing → fixing → testing again. Each write currently sends the entire file as input. Most M5 calls are these iterative writes.
- A `str_replace`-style tool would compress input by 3-4× on iterative writes. For a 250-line implementation file iterated 4 times: 1180 → 340 input lines.
- Hatter's M4 file authoring would also benefit (writes test files in passes), though he's a smaller share of cost.
- Composes naturally with tool-call event surfacing ([33e29f5c](../.daedalus/roadmap/items/33e29f5c)) — once tool calls are visible in the bus, we can measure the iterative-vs-one-shot ratio cleanly.

Expected outcome: re-running v3's directive after diff tools land brings total cost to maybe $3.20-$3.50 — comparable to or below the v6 banner parallel-TDD baseline, while keeping serial's per-feature artifact coherence.

## What ships next

1. **Analysis 031's framing correction**: the "Hatter sprawl is the cost driver" assertion in 031 F3 was wrong; v3's per-agent telemetry shows Tweedles' iterative-file-writes dominate. This analysis (032) supersedes that finding.

2. **No more directive iteration on tdd-serial** for now. v3's directive is the right shape; further compression requires substrate work (diff tools, tool-call events). Iterating directives further would be premature.

3. **Roadmap items filed during this run cluster** (analyses 031 + 032):
   - [3925b46f](../.daedalus/roadmap/items/3925b46f) P1 bug — Quiescence tracks in-flight `deliberate()` calls
   - [92cec468](../.daedalus/roadmap/items/92cec468) P1 bug — Substrate divergence: bus vs disk
   - [33e29f5c](../.daedalus/roadmap/items/33e29f5c) P1 feature — Surface tool calls to bus event log
   - [884bbad2](../.daedalus/roadmap/items/884bbad2) P2 bug — Empty-response parse errors
   - [0b785ab0](../.daedalus/roadmap/items/0b785ab0) P2 feature — Parallelize per_item iterations
   - [51fe6dc5](../.daedalus/roadmap/items/51fe6dc5) P2 feature — Test scenario prioritization
   - [0858a936](../.daedalus/roadmap/items/0858a936) P2 feature — Diff-based write tool

4. **Banner status**: tdd-serial is now a completable workflow on the same directive that the parallel-TDD v6 banner used. Cost premium remains (~32%) but the serial workflow ships an end-to-end Pomodoro app + comprehensive deferred-test backlog + working M6 review-and-fix loop. Worth being a recommended workflow choice for projects where:
   - Feature batches make sense (one-at-a-time iteration is the user's preference)
   - Per-feature artifact coherence matters more than total wall-clock
   - The deferred-test backlog is itself valued (e.g., the test prioritization feature ships)

5. **Pivot back to P8.3** (streaming + Mock Turtle) — the foundation P8.4 live-watch needs. The directive iteration on tdd-serial is finished for now; the substrate work to make tool calls and in-flight deliberations visible is next-priority but doesn't block streaming.

## Summary

v3 is the win. Composability primitive lives. Directive bound on Tweedles compresses M4 below v1 baseline. M5 iter 1 settles naturally at half v1's cost. M6 runs a full review-and-fix loop for the first time. End-to-end completion at $4.72 produces a working Pomodoro app with reviewed and bug-fixed code.

But the cost story analysis 031 told was wrong: Hatter wasn't the bottleneck. Tweedles iterating on file writes via `write_file` in M5 + M6 dominate cost (72%). The right next compression isn't more directive engineering on Hatter's per-iteration test-scenario count — it's substrate work on tool-call observability + diff-based file authoring.

The serial workflow pays a real cost-and-wall-clock tax vs parallel-TDD. That tax buys per-feature artifact coherence, a deferred-test backlog, and the foreach primitive Wonderland needs anyway. Whether it's *worth* paying is a directive-by-directive judgment; the workflow is a real tool now whether or not it's the cheapest one.
