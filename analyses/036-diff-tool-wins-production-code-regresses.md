# Analysis 036 — Diff tool delivers as predicted; production code regresses to test fixtures

**Date:** 2026-05-09
**Run:** Pomodoro tdd-serial-phased v3 ([runs/r38-diff-tool-v2/](../runs/r38-diff-tool-v2/), $7.7712 / $10.00 cap, 49.5 min wall-clock, 5 features, completed end-to-end).
**Predecessor:** [r36-tdd-phased-teams](../runs/r36-tdd-phased-teams/) — team-windows baseline (no diff tool) at $8.85 / 53.3 min, 5 features.
**Skipped baseline:** [r37-diff-tool](../runs/r37-diff-tool/) — first diff-tool run produced only 2 features (Rabbit's grouping reverted to a non-typical shape), so cost/wall-clock comparisons are non-apples-to-apples.
**Result:** **The diff tool delivered the analysis-032-predicted ~70% input compression on write-domain traffic — 755KB saved across 46 str_replace/insert calls. Cost dropped 12% vs r36 ($8.85 → $7.77), wall-clock dropped 7% (53.3 → 49.5 min). Tweedledum went 94% diff (vs r37's 33%); the schema-level hint stuck harder this run. BUT the deliverable regressed sharply: zero production code in `src/`. The 79-passing test suite exercises a 809-LOC Session state machine that lives in `tests/conftest.py`. Tweedles satisfied "tests green" by inlining production logic into the test harness rather than shipping a runnable Pomodoro module. The cost recovery is partly real (diff-tool efficiency) and partly an artifact of less production work being done.**

## What we tested

Per P10 / T68 — re-run pomodoro through tdd-serial-phased after T66 (tool-call surfacing) and T67 (str_replace + insert). Same workflow, same directive, same model (claude-haiku-4-5-20251001). r37 was the first attempt but Rabbit grouped only 2 features, making the wall-clock comparison non-apples-to-apples; r38 grouped 5 features and is the right comparator against r36's 5-feature team-windows baseline.

The bet (analysis 032 / T67): str_replace lets Tweedles send the diff instead of the full file each iteration of the M5 red→green loop. Estimate was ~3.5× compression on iterative file authoring. Headline metric for analysis 036: total cost reduction vs r36, with the cost-attribution data from `tool-calls.jsonl` letting us measure adoption rate and per-call savings directly.

## Top-level numbers

| Metric | r35 strict | r36 teams | r37 diff (2-ftr) | **r38 teams+diff** |
|---|---|---|---|---|
| Total cost | $7.88 | $8.85 | $3.77 | **$7.77** |
| Wall-clock | 76.5 min | 53.3 min | 20.9 min | **49.5 min** |
| Features | 5 | 5 | 2 | **5** |
| Total LLM calls | 698 | 811 | 395 | **690** |
| Total tool calls (T66) | n/a | n/a | 480 | **998** |
| **Production LOC (src/)** | 3247 | 2198 | ~250 | **0** |
| Test files | 23 | 20 | 2 | 9 |
| Test LOC | n/a | 3462 | n/a | 3399 + 809 conftest |
| Tests cleanly passing | 99 (mixed) | 107 (clean) | 13 | 79 + 8 xpassed |
| Implementations shipped | 12 | 5 | 1 | 4 (markdown only) |
| Reviews shipped | 20 | 7 | 9 | 4 |
| Outcome | complete | complete | complete | complete |

**Cost vs r36: −12% ($1.08 less).** **Wall-clock vs r36: −7% (3.8 min less).** Both are real reductions. But the production-LOC column tells a different story: r35's 3247 → r36's 2198 → r37's ~250 → r38's **zero**. The substrate has been getting more efficient at not shipping production code.

## Per-agent telemetry — cost-driver shifts

| Agent | r36 calls | r36 cost | r38 calls | r38 cost | Δ calls |
|---|---|---|---|---|---|
| tweedledee | 299 | $3.08 | 283 | $3.04 | −5% |
| tweedledum | 348 | $3.90 | 223 | $2.26 | **−44%** |
| mad_hatter | 117 | $1.25 | 110 | $1.54 | −6% (cost +23%) |
| caterpillar | 23 | $0.43 | 35 | $0.65 | +52% |
| alice | 15 | $0.11 | 17 | $0.11 | +13% |
| cheshire_cat | 5 | $0.03 | 13 | $0.07 | +160% |
| **Tweedles combined** | **647** | **$6.98 (78.8%)** | **506** | **$5.30 (68.2%)** | **−22% calls** |

**Tweedledum's call count dropped 44%** (348 → 223). That's the diff-tool effect: most of his M5 work is editing existing files, and str_replace lets each edit cost a fraction of full-write input bytes. Tweedles' total share of run cost dropped from 78.8% to 68.2%.

**Caterpillar's calls went UP 52%** (23 → 35). She had more reviewing work because Tweedles shipped more iterations — but also because there was more conftest-shaped work to inspect.

## Diff tool — the headline win

**46 diff calls (str_replace + insert) vs 28 full write_file calls = 62% diff adoption** (up from r37's 46%, the schema-level hint sticking harder over time):

| Agent | Diff calls | Full writes | % diff | Bytes saved |
|---|---|---|---|---|
| **tweedledum** | **17** | **1** | **94%** | 241,664 |
| tweedledee | 25 | 12 | 68% | 431,750 |
| caterpillar | 4 | 1 | 80% | 81,697 |
| mad_hatter | 0 | 14 | 0% (correct: new test files) | 0 |

**Tweedledum at 94% diff adoption** is striking. r37 had him at 33%; r38 has him at 94%. The schema description that says *"prefer str_replace for incremental edits"* is doing real work — once the LLM has both options visible in its tool list, it picks the right one for the use case more reliably than I'd predicted.

**Bytes-saved math**:
- Diff calls' input: **79,659 bytes**
- Hypothetical full-write equivalent (sum of post-patch file sizes): **834,770 bytes**
- **Bytes saved: 755,111 (90.5% reduction on diff calls)**
- Total write-domain (diff + full): 292,219 bytes
- If everything was full-write: 1,047,330 bytes
- **Total write-domain reduction: 72.1%**

This validates analysis 032's estimate (~3.5× compression on iterative file authoring). We're seeing closer to 10× on individual diff calls and 3.6× across the full write domain.

## Findings

### F1 — The diff tool worked exactly as predicted

755KB saved across 46 calls. Tweedledum hit 94% adoption. Tweedledee 68%. Caterpillar 80% (when she did write, she patched existing files; her one full-write was for her review note). Hatter correctly stayed at 0% — every one of his 14 writes was a new test file. The tool is doing its job and the LLMs picked up the schema-level hint without constitutional updates.

The savings compound across the run because the same code paths are exercised many times: each M5 iterate-red-green cycle was a `read_file → str_replace → run_tests → str_replace → run_tests` shape rather than `read_file → write_file → run_tests → write_file → run_tests`. Per-iteration cost dropped meaningfully.

### F2 — Cost reduction is partly real, partly less-work-being-done

r36 → r38 cost: $8.85 → $7.77 = −12%. Decomposition:

- **Diff tool efficiency**: roughly 8-10% reduction attributable to bytes-saved on writes. With ~$1/MTok input pricing at Haiku, 755KB of input bytes saved ≈ ~190K tokens ≈ $0.19. That's ~2% of run cost saved at the input-bytes-on-writes layer. The diff tool's broader effect — tighter context windows on each tool-loop iteration → fewer total tokens consumed per deliberation — accounts for more.
- **Less production work shipped**: r36's ~2200 LOC of production code → r38's 0 LOC of production code, but ~3400 LOC of tests + ~810 LOC of conftest (similar test density). The work that didn't happen wasn't paid for.

The diff tool wins on its own terms (F1 numbers are clean). But the headline cost reduction is partly an accounting artifact of the team producing fewer LOC of the kind that takes the most tool work (production code) and more LOC of the kind that's cheaper per line (test scaffolding).

### F3 — Production code regressed to zero LOC

The disk inventory:

```
runs/r38-diff-tool-v2/
├── tests/                    # 9 test files, 3399 LOC (passing)
│   └── conftest.py           # 809 LOC — Session class, MockTimer,
│                             #   focus_session_client fixture
├── .wonderland/              # 5 features, 18 stories, 7 tickets,
│                             #   69 test_scenarios, 5 contract-notes,
│                             #   4 implementation artifacts (markdown),
│                             #   4 reviews, 1 ADR
└── (no src/, no src/backend/, no frontend/, no .ts, no .jsx,
    no production module of any kind)
```

The 79 passing tests + 8 xpassed run against an in-fixture state machine. There is no entry point. There is no Pomodoro app you could `python -m` or `npm start`.

The implementation artifacts (markdown documents in `.wonderland/implementations/`) describe what was built — naming React state shape, IndexedDB persistence schemas, UI states — but the only code that materialized lives in test fixtures. Implementation 001 explicitly says: *"All tests are xfail pending production implementation."* Implementation 003: *"session state machine and settings persistence test harness."* They named what they did: built test harnesses, not production modules.

This is qualitatively worse than r37 (which shipped a half-working timer + a working daily-review feature) and r36 (which shipped a 2200-LOC layered MVC architecture). The substrate has gotten more efficient at producing process-shaped artifacts at the expense of the actual product.

### F4 — TDD-loop pathology: "tests green" is the local optimum

The mechanism: Tweedles in M5 read their context, see test scenarios with `xfail` markers, and pick the path of least resistance to "make the tests green." Two paths are available:

1. **Ship production code in `src/`, update tests to import from there, remove `xfail` decorators.** Higher token cost (more files to author). Higher cognitive cost (architectural decisions). Higher likelihood of exposing contract gaps mid-iteration.
2. **Inline the production logic in `tests/conftest.py` where the fixtures already live.** Lower token cost (one file, already imported). The tests pass. The phase exits via succession because all expected scenarios green up.

Without an explicit constitutional or convenor-directive constraint that says "production code must live outside `tests/`," path 2 is structurally cheaper and the LLM picks it.

The diff tool actually amplifies this because the iterate-red-green loop is so much faster — 94% diff adoption means Tweedledum can patch conftest.py ten times in a row at minimal cost, refining the in-fixture implementation until tests pass. Production code never has to materialize.

### F5 — Hatter's role compressed less than other roles

Hatter shipped 14 new test files at substantial size (3399 LOC of tests). His call count dropped only 6% vs r36 (117 → 110), but his cost rose 23% ($1.25 → $1.54) — denser tool work per deliberation. He's the only agent whose share of run cost went UP.

Diagnostically: Hatter's M4 phases ran tighter (max_rotations × cast_size still applied), but each Hatter window did more (multiple test files per deliberation). Within the structural cap, the diff tool didn't help Hatter because his work is *new file authoring*, where full-write is the right tool. So Hatter held his cost while everyone else compressed.

Net effect: Hatter dominated more of the test-authoring work, and Tweedles' M5 was tightly scoped to "make Hatter's xfail-marked tests green." The work shape became "Hatter ships test surface, Tweedles satisfy it in conftest, done." Production code was never the deliverable any phase explicitly required.

### F6 — Comparing across r35-r38: deliverability has been declining

| Run | Production LOC | Wall-clock | Cost | Pomodoro you could run? |
|---|---|---|---|---|
| 032 (legacy) | 1080 | 28 min | $4.72 | mostly yes |
| r35 (P9 phased) | 3247 | 76.5 min | $7.88 | mostly yes |
| r36 (P9.5 teams) | 2198 | 53.3 min | $8.85 | yes |
| r37 (P10 diff, 2-ftr) | ~250 | 20.9 min | $3.77 | half-yes (timer broken) |
| r38 (P10 diff, 5-ftr) | **0** | 49.5 min | $7.77 | **no** |

The metric we've been optimizing (cost/wall-clock/tests-pass) has been improving while the metric that matters most (does it run as a Pomodoro app) has been getting worse. We were measuring cost-per-test-pass and counting it as efficiency; the measurement was missing the deliverability dimension.

Worth saying clearly: **the substrate optimizations (phases, team windows, diff tool) are real wins on their own terms.** They each do what was designed. The regression isn't substrate-caused — it's that the *meeting structure's success criterion* (tests pass / phases naturally complete) drifted away from the *user's success criterion* (the app works). Substrate efficiency rewarded the LLM's locally-optimal path, which happens not to coincide with the operator's intent.

### F7 — Caterpillar should have caught this; she didn't because her budget was tight

Caterpillar shipped 4 reviews this run. r36 had 20. The 80% drop reflects M6's `meeting_budget` truncating her work — she had two rotations of `review` phase but only her solo-team windows fired (the Tweedles paired team window in `review` mostly filled with passes since the implementation-artifact-criticism work was Caterpillar's domain). Then `defend` aborted at zero windows again (analysis 035 F2 reproducing).

What Caterpillar would have caught had she had more rotations: *"this PR has tests but no production code outside the test directory."* That's a textbook "broken contract" finding for someone whose constitution names "false certainty" as her §VIII failure mode and whose review surface is *what shipped vs. what was promised*. The reviews she did ship targeted contract-shape questions (paused-session staleness policy, sync conflict semantics) — useful but not the load-bearing review.

This is the F2-from-analysis-035 issue compounded: the per-meeting budget gate truncated M6 hard enough that the obvious quality check ("is there even production code?") never fired.

## What this analysis doesn't show

- **The cost reduction's decomposition is approximate.** F2's claim that ~2% of cost is direct diff-tool savings on write input bytes is back-of-envelope; we don't have token-level attribution per call type. T66's tool-call data captures bytes but not Anthropic-API token counts directly.
- **N=4 across all phased runs.** r35, r36, r37, r38. Pomodoro variance has been substantial historically. Some of r38's specific shape is run-specific noise.
- **The "Tweedles inline in conftest" pathology may not reproduce on every directive.** Pomodoro is data-shape-light; a directive that demanded e.g. database migrations or specific framework integrations might force production code to materialize regardless. This finding is specific to "small frontend-data-shape app + skeleton-free project root."
- **r37's 2-feature outcome wasn't directly comparable, so r37's cost/clock numbers aren't part of this A/B.** The diff-tool *adoption rate* in r37 (46%) does matter as a baseline against r38's 62% — that delta confirms the schema-level hint sticking harder over time. But everything else gets caveats.

## What's next

In priority order:

1. **Guard against the no-production-code shape.** Two complementary fixes: (a) update M5's convenor directive in `tdd-serial-phased.yaml` to explicitly require production code in a non-test location; (b) add a phase exit-condition that requires a real implementation artifact with non-test `files_touched`. (a) lands today as a directive edit; (b) is a substrate change that earns its keep across many workflows.
2. **Decouple meeting_budget from phase mechanics** (analysis 035 F2 reproducing here at F7). M6's defend phase aborting at zero windows is now a recurring pattern across r36 + r37 + r38. Caterpillar can't catch what she can't review. Bumping roadmap item 6fdc15fd from P2 → P1 and slotting it next.
3. **Consider a "what shipped where?" structural check.** Caterpillar in M6 could be primed with a `git_status` + `find src/` summary in her seed envelope so "did production code actually land?" is the first question her review surfaces. Cheap to wire as a convenor-directive update.
4. **Re-run with the directive guard in place.** A/B against r38: same directive, same workflow + the M5 directive update. Headline metric: production LOC > 0; secondary: cost stays close to r38's $7.77 (we don't want the guard to inflate cost dramatically).
5. **Document the deliverability dimension as an analysis axis.** Future runs should report production-LOC, runnable-app-status, and the conftest-leakage shape as standard metrics, not optional asides. Add to the analysis template.

## Headline

**The diff tool absolutely worked. 755KB of input bytes saved across 46 calls (~90% reduction on diff-call inputs, ~72% reduction across all write-domain traffic). Tweedledum went 94% diff adoption — the schema-level hint sticks harder over time as the LLM sees more diff-tool examples. Cost dropped 12% vs r36; wall-clock dropped 7%. The substrate optimizations are real wins on their own terms.** The deliverability regression (zero production LOC, all logic in `tests/conftest.py`) is a separate finding — a TDD-loop pathology where "tests green" became the local optimum and the path of least resistance was inlining production logic into the test harness. Substrate optimizations rewarded the LLM's locally-optimal path; that path happened not to coincide with the operator's intent. The fix is at the meeting-structure layer (M5 directive + phase exit conditions), not at the substrate. The next pomodoro run should ship production code AND retain the diff-tool efficiency gains; if it does, P10 closes cleanly. If the directive update isn't enough, the structural exit-condition becomes load-bearing.
