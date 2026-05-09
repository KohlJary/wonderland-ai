# Analysis 031 — TDD-serial v1: per_item iteration validates the substrate, exposes the directive ceiling

**Date:** 2026-05-08
**Run:** Pomodoro tdd-serial v1 (killed at $4.01 / $5.00 budget cap warning, ~24 min wall-clock).
**Snapshot:** [analyses/data/031-tdd-serial-v1/](data/031-tdd-serial-v1/) — manually captured (run was killed before the script's snapshot pass).
**Result:** **The per_item iteration substrate works cleanly. Per-feature output quality is observably better than parallel-fan-out. Cost remains TBD because Hatter's §VIII sprawl is now the dominant cost driver — and it's directive-shaped, not workflow-shaped. Wall-clock is ~3× parallel-TDD; parallelization is the future-direction. Four roadmap items filed.**

## What we tested

The hypothesis from the tdd-serial workflow's design document: **per-feature M4/M5 iteration should be cheaper, more focused, and produce better output than parallel-fan-out** (the existing tdd workflow's shape, which pins all features into one M4 + one M5). The cheapness argument rested on cache locality (smaller per-iteration payloads) and focused attention (no Hatter sprawl across 5 features at once). The composability primitive — `per_item: feature` as the foreach Wonderland needs anyway — was the orthogonal win regardless of cost outcome.

The substrate ([commit 651cb64](../../../commit/651cb64)):
- `Meeting.per_item: str | None` declares the iteration kind
- `resolve_seeds()` slices iteration-kind seeds to the current item, routes per_item-meeting seeds through the paired iteration thread, rewrites multi-artifact utterances to keep only the matching one
- `run_workflow()` detects per_item meetings and convenes once per item with `thread_id = {meeting.id}-{slug}`
- `MeetingStartEvent` / `MeetingEndEvent` carry iteration metadata (the surface P8.4's live-watch screen will render)

The workflow ([closet/workflows/tdd-serial.yaml](../src/wonderland/closet/workflows/tdd-serial.yaml)):
- M1 / M2 / M2.5 / M3 unchanged from canonical TDD
- M4 + M5 marked `per_item: feature`, per-iteration `meeting_budget: 0.50`
- M6 unchanged — sees combined working tree at the end

The test directive matches the substrate-convergence iterations (analysis 029 v6 banner) for direct apples-to-apples comparison: *"Build a Pomodoro timer app: focus sessions, configurable breaks, daily review, persistent settings."*

## Per-meeting + per-iteration cost

| Meeting | Iteration | Cost | Calls | Time | Outcome |
|---|---|---|---|---|---|
| M1 (Caucus Race) | — | $0.0320 | 2 | 20.2s | COMPLETE |
| M2 (Rabbit's Errand) | — | $0.0667 | 8 | 33.7s | COMPLETE |
| M2.5 (Caterpillar) | — | $0.0245 | 4 | 9.0s | COMPLETE |
| M3 (Tweedles) | — | $0.1408 | 14 | 118.3s | COMPLETE |
| **M4 (Tea Party)** | 1 — Focus Session Timer | $0.5045 | 57 | 167.7s | MEETING_BUDGET |
| M4 | 2 — Break Timer | $0.5255 | 51 | 156.6s | MEETING_BUDGET |
| M4 | 3 — Daily Review | $0.7239 | 84 | 300.3s | MEETING_BUDGET |
| M4 | 4 — Persistent Settings | $0.5938 | 65 | 184.2s | MEETING_BUDGET |
| M4 | 5 — Streak/Gamification | $0.6976 | 62 | 179.1s | MEETING_BUDGET |
| **M5 (Implementation)** | 1 — Focus Session Timer | $0.6982 | 56 | 226.1s | MEETING_BUDGET |
| M5 | 2 — Break Timer | (killed) | | | killed at $4.01 |
| **Total to kill** | | **$4.01** | **403** | **~24 min** | |

Per-iteration M4 average: $0.61, 64 calls, 198s (over the $0.50 cap on every iteration). Per-iteration M5 (iter 1 only): $0.70.

## Comparison vs analysis 029 v6 banner ($3.56, parallel-TDD on the same directive)

| Metric | tdd-serial v1 (killed) | parallel-TDD v6 banner | Delta |
|---|---|---|---|
| M1-M3 cost | $0.265 | $0.20 | +$0.07 |
| M4 cost | $3.045 (5 iterations) | $1.22 (1 meeting) | **+$1.83** |
| M5 cost | $0.698 (1 of 5 iterations) | $0.53 (1 meeting) | est. +$2.97 if all 5 ran |
| M6 cost | (didn't reach) | $1.61 | n/a |
| **Estimated total if completed** | ~$7-8 | $3.56 | **+$3-4 (2× expensive)** |
| Wall-clock | ~24 min through M5 iter 1 | ~9 min total | ~3× slower |
| Production code shipped | 1168 LOC | similar (~1200 LOC) | neutral |
| Test coverage | 1102+ LOC across 15 files | similar (~1100 LOC across ~6 files) | more files, similar test count |

The cost story is unambiguous in this run: serial is **substantially more expensive** than parallel, not less. The cache-locality hypothesis was wrong as stated. The per-iteration payloads *are* smaller, but Hatter's sprawl per feature is roughly the same as his sprawl across all features in the parallel case, and now you pay for it five times.

## What worked structurally (the substrate findings)

### F1 — per_item iteration substrate is correct

Every iteration convened cleanly with `thread_id = test-scenarios-{slug}` / `implementation-{slug}`. Seed slicing delivered exactly one feature per iteration's envelope (verified by inspection of the M4 iteration starts — each Dodo directive line showed the single feature artifact threaded through). The paired-iteration filter (M5 iteration N seeding from M4 iteration N's thread) worked: M5 iter 1's seeds were 4 utterances drawn from `test-scenarios-focus-session-timer` thread plus the broader feature/contract context, exactly as designed.

No cross-iteration event leaks (the [analysis 030](030-directive-bounds.md) `terminal_thread_id` fix held). No malformed thread IDs. The composability primitive ships clean.

### F2 — per-feature output quality is observably better

Test files are scoped per feature (`test_focus_session_timer_*.py` × 5 files for feature 001, `test_break_timer_*.py` × 2 for feature 002, etc.). Each file is internally coherent. Cross-feature concerns are deferred cleanly when they appear:

```python
def test_focus_session_completion_triggers_event_logging(self, client):
    """When a session completes (via timeout or skip), an event is logged
    for later consumption by daily review (feature 003).
    Minimal test: session completion POSTs to /api/sessions/<id>/complete,
    and the event is persisted."""
    pytest.skip("Event logging contract defined in feature 003; tested there")
```

That `pytest.skip("tested there")` is the right move under per-iteration scope — the substrate enabled it. In the parallel-TDD run, the same scenario would have either bloated feature 001's test file with feature 003 setup or been silently dropped between features. The bounded scope made the cross-feature deferral *legible*.

Compare to v6 banner's M4 output: tests were grouped by axis (happy-path vs fragility) but spanned all 5 features in single files. Per-iteration scope produced files-per-feature, which scales better when feature counts grow. Quality compounds with feature count, not just absolute test count.

## What didn't work (the directive + behavioral findings)

### F3 — Hatter's §VIII sprawl is the dominant cost driver, and it's directive-shaped

The cache-locality argument was wrong because Hatter sprawls *within* an iteration as much as he ever did across features. For Focus Session Timer alone he produced **5 test files × ~10 tests = ~50 tests**. The fragility file alone had 12 tests across 6 classes (tab blur, audio handling, duration boundaries, MS precision, page-reload persistence). Every test is a real failure mode; the §VIII guard ("severity inflation, scenario sprawl") didn't fire because the sprawl wasn't toward severity inflation — it was toward category breadth.

The substrate-side bound (per_item delivers exactly one feature in context) earned its keep. The behavioral-side bound (the directive language asking for "the load-bearing edge cases that match the feature's failure-mode profile") didn't. Per-iteration scope bounded *what* he reasoned about, not *how much* he reasoned within that scope.

This is a directive-engineering problem, not a workflow-architecture problem. The next-run refinements:

1. **Surface-relative orienting prior**: "The number of scenarios should match the feature's surface area, not the number of edge cases you can imagine. A feature with a single user action wants a small handful of happy-path + a small handful of fragility scenarios. A feature with multiple state transitions, persistence, or cross-system effects wants more. Calibrate to the feature, not to the abstract space of imaginable bugs."

2. **Self-audit per scenario**: "Before you ship each scenario, audit it against three questions: (a) Would this test, if it failed, surface a bug an actual user would notice? (b) Does an earlier scenario already pin the same behavior or catch the same class of bug? (c) Is this scenario describing a real failure mode for *this* feature, or a generic edge case I'd ship for any feature? If you can't say yes to the first — or if either of the others is yes — don't ship the scenario. Skipping a scenario is a healthy move; sprawling is the failure mode."

Hardcoding a scenario count was the rejected alternative — too rigid for a YAML used across directives where feature surface area legitimately varies.

### F4 — Tweedles default to shipping production code in M4

The directive explicitly says "do NOT write production code in this thread" for Tweedles in M4. Across iterations 1, 2, 4, 5, Tweedles consistently tried to ship `implementation` artifacts during M4. Most got caught by the late-publish guard after thread close (suppressed); one landed on-thread in iteration 4 (the `implementation×1` count for Persistent Settings, which produced 777 LOC of frontend code: `SettingsScreen.tsx` + `settings.ts` + `settings.test.ts`).

The pattern: Tweedles read Hatter's tests, immediately want to implement against them, and the closest "useful work" disposition becomes "ship code." The negative directive ("don't write code") doesn't suffice because it leaves no clear positive work-product for them in M4.

The directive refinement: **frame their M4 work-product positively.** "Your role in M4 is test-clarification, not implementation. Read each test as it ships and ask: do the contracts make this test answerable? If a contract has gaps that affect testability — a state transition that's named but undefined, a payload field that's mentioned but unspecified — surface those as concerns or contract-note revisions before M5 starts. M5 is your turf for implementation; this thread is where you make sure the test surface is implementable." That gives them something to do that isn't "default to shipping code."

### F5 — Wall-clock penalty is ~3× parallel, and it's structural

The substrate runs serially: iteration 2 doesn't start until iteration 1 closes. For 5 features that's 5×~180s = ~900s for M4 alone, vs ~350s for parallel-TDD's single M4. Even with refined directives compressing each iteration ~30-40%, the M4 inner loop is 10+ min serial vs ~5 min parallel.

This compounds painfully with the TUI live-watch UX (P8.4): staring at one iteration progress bar for 20+ minutes is bad UX; watching 5 cells fill in over ~3 minutes is the experience we want. The parallelization roadmap item ([roadmap entry 0b785ab0](../.daedalus/roadmap/items/0b785ab0)) gets sharper teeth from this run — per-iteration independence (same M3 contracts in, disjoint feature files out) makes asyncio.gather natural; the only real concern is shared-infrastructure write contention (e.g., `src/backend/api/__init__.py` router registration from two iterations at once), addressable with feature-disjoint paths or a serialized integration hook.

### F6 — Substrate divergence: bus event accounting undercounts disk reality

Two iterations (M4 iter 3 Daily Session Review, M4 iter 5 Streak/Gamification) ended with **0 test_scenario artifacts on the bus** — but disk had real test files. For Daily Session Review: `test_daily_review_*.py × 3 = 954 LOC`. For Streak: `test_streak_*.py × 3`. Hatter's `write_file` tool calls landed; the structured speech-act emission that would have shipped a `test_scenario` artifact on the bus failed (correlated with parse-error empties from F7 below).

Late-publish messages contained the giveaway: `[bus record coerced to implementation: write_file calls landed for tests/test_X.py]`. The framework recognized the divergence at suppression time but didn't reconcile it.

Why this matters: downstream meeting seeds use the bus capture. M5 iteration N's seed binding `from: test-scenarios, kinds: [test_scenario, story]` returns nothing for the divergent iterations, so M5 has to rely on Tweedles using `read_file` to discover Hatter's tests. Works, but fragile. Analyses + telemetry undercount actual output. The "iteration produced no artifacts" framing reads as degenerate when in fact substantive work shipped.

Filed as [roadmap entry 92cec468](../.daedalus/roadmap/items/92cec468). Fix shape: synthesize a bus-visible record from the disk side effect when the speech-act emission fails.

### F7 — Empty-response parse errors compound under sustained iteration

Three empty-response parse errors across 6 iterations (50% rate):
- M4 iter 3 — Hatter (Daily Session Review)
- M4 iter 4 — Tweedledum (Persistent Settings)
- M5 iter 1 — Tweedledum (Focus Session Timer)

The Anthropic API returned `len=0` strings with no JSON block. The parse-retry substrate ([analysis 023](023-quiescence-and-split-phases.md) fix) caught and retried; sometimes recovered (iter 4, iter M5-1), sometimes didn't (iter 3). Worst case (iter 3): Hatter's parse-retry chain didn't produce a usable speech-act emission, even though the file write side effect landed (compounds with F6).

Hypotheses worth investigating: cumulative episodic-memory context across iterations without compaction; specific prompt shapes triggering the model's silent-decline behavior; Anthropic API instability we're not surfacing usable headers from. Filed as [roadmap entry 884bbad2](../.daedalus/roadmap/items/884bbad2).

### F8 — Quiescence-fires-fast still suppresses substantive work

Six late-publish suppressions across the run, all with substantive content the team could have used:
- M1: Cat ADR proposal ("Five user stories accumulated... imply a non-trivial seam"); Queen security/compliance assessment
- M3: Tweedledee feature-layout question; Tweedledum response covering all five contract backend impacts
- M4 iter 1, 2, 4, 5: various Tweedle implementation/contract attempts; Hatter cross-feature questions
- Iteration 5: Alice concern about contract ambiguities blocking M5

The pattern is consistent across analyses 026-031: the ThreadMonitor's quiescence detector fires when (a) bus is silent and (b) no open expectations, but agents have outstanding `deliberate()` coroutines that haven't shipped yet. Bus is silent because they're still thinking, not because they're done. The late-publish guard correctly catches the orphans (no data corruption), but the team loses substantive contributions.

Filed as [roadmap entry 3925b46f](../.daedalus/roadmap/items/3925b46f) at P1 — needs to ship before P8.4 (live-watch) lands so the UI doesn't render premature-close-then-late-suppress as visible event pairs. Fix shape: surface in-flight `deliberate()` coroutines to the ThreadMonitor as additional open-expectation source.

## What the run accomplished beyond the substrate validation

**Production code shipped** (1168 LOC across 8 files):
- `src/backend/api/sessions.py` (NEW, 188 LOC) — Focus Session Timer backend
- `src/backend/models.py` (+144 LOC modifications)
- `src/backend/api/__init__.py` (+/-23 LOC router wiring)
- `frontend/src/SettingsScreen.tsx` (NEW, 273 LOC)
- `frontend/src/settings.ts` (NEW, 225 LOC)
- `frontend/src/__tests__/settings.test.ts` (NEW, 279 LOC)
- `frontend/src/App.tsx` (+137 LOC modifications)
- `src/backend/api/messages.py` (template removal)

**Test coverage** (1102+ LOC across 15 files):
- 5 files for Focus Session Timer (happy-path / backend / frontend / state-machine / fragility)
- 2 files for Break Timer (happy-path / fragility)
- 3 files for Daily Review (happy-path / fragility / realtime)
- 2 files for Persistent Settings (happy-path / fragility)
- 3 files for Streak (happy-path / fragility / daily-happy-path)

**Wonderland artifacts** (in `.wonderland/`):
- 1 ADR
- 5 features (one per user-facing capability)
- 5 stories + 2 stretch personas (Maya, Derek)
- 12 tickets
- 8 contract notes (5 main + 3 sub-features for streak)
- 35 test_scenarios (the Hatter sprawl, made legible)
- 2 implementations (settings + streak frontend)

The run is a partial banner: feature 001's backend is real and likely tests-green; features 002-005 have tests but no implementation (M5 only ran iteration 1 before kill). This is genuinely useful artifact tree for analyzing the framework's per-feature coherence.

## What ships next

1. **Directive refinements** ([commit pending] on feat/tdd-serial branch):
   - M4: Hatter surface-relative + self-audit clauses (F3 above)
   - M4: Tweedles positive work-product framing (F4 above)
   - Both stay domain-agnostic — no Pomodoro-specific anchor

2. **Roadmap items already filed**:
   - [3925b46f](../.daedalus/roadmap/items/3925b46f) P1 bug — Quiescence tracks in-flight `deliberate()` calls
   - [92cec468](../.daedalus/roadmap/items/92cec468) P1 bug — Substrate divergence: bus accounting vs disk reality
   - [884bbad2](../.daedalus/roadmap/items/884bbad2) P2 bug — Empty-response parse errors compound
   - [0b785ab0](../.daedalus/roadmap/items/0b785ab0) P2 feature — Parallelize per_item iterations

3. **Re-run with refined directives** for the cost-comparison: same Pomodoro directive, tdd-serial v2. Expected to land cheaper than v1 (Hatter sprawl bounded), still ~2-3× parallel-TDD on wall-clock until parallelization ships.

## Summary

The composability primitive lives. `per_item: feature` works as designed; per-feature artifact coherence is observably better than parallel-fan-out. The cache-locality cost-savings hypothesis was wrong as stated — the per-iteration payload shrinks but Hatter's sprawl-per-iteration remains the cost driver, and now you pay for it N times. That's a directive-engineering problem, not an architecture problem.

The wall-clock tax is real and structural; parallelization is the future-direction that closes the gap (and makes the live-watch UX viable).

Four roadmap items file the structural bugs this run surfaced: in-flight deliberation tracking, bus-vs-disk reconciliation, empty-response retry hardening, and per_item parallelization. None block the directive refinement work; that ships next on `feat/tdd-serial`.

This is the wash case I named in advance — composability primitive earned its keep, cost story didn't materialize the way the hypothesis predicted, but every finding is actionable and the next run is well-aimed. The serial workflow is a real tool now whether or not it ends up cheaper than parallel.
