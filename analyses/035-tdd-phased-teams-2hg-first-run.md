# Analysis 035 — Team windows first run: wall-clock recovers 30%, cost worsens, output quality up, substrate tension surfaces

**Date:** 2026-05-09
**Run:** Pomodoro tdd-serial-phased v2 ([runs/r36-tdd-phased-teams/](../runs/r36-tdd-phased-teams/), $8.8537 / $5.00 cap, 53.3 min wall-clock, completed end-to-end).
**Predecessor:** [r35-tdd-serial-phased](../runs/r35-tdd-serial-phased/) — strict-serial baseline ($7.88 / 76.5 min) for the apples-to-apples A/B.
**Result:** **First live run of team windows (P9.5 / T64). Output quality up substantially: 107 cleanly-passing tests vs r35's 99 (where 84 were xpassed-because-xfail-decorator-uncleared bookkeeping); pure-Python layered MVC architecture vs r35's Python+TS shadow-implementation hack; broader feature coverage (all 5 features vs r35's depth-on-2). Wall-clock dropped 30% (76.5 min → 53.3 min) per analysis 034 F2's prediction. Cost rose 12% ($7.88 → $8.85) — the right direction given quality is up; cost reflects how much structural work the run actually shipped. The substrate gap surfaced: 10 of 18 phases aborted via meeting_budget, including M6's defend phase at zero windows, leaving Caterpillar's review findings unaddressed. Phase events finally on disk (T58d): Hatter shipped 9 deliberations across all 5 M4 iterations — the structural cap was real all along; "Hatter calls" was the wrong unit to measure.**

## What we tested

Per analysis 034 F2 / P9.5 / T64-T65. Same Pomodoro directive as 032 and r35; same model (claude-haiku-4-5-20251001). Workflow: `tdd-serial-phased` with `team_groupings:` declarations on every phased meeting:

| Meeting | Phase | Cast | Teams | Concurrent windows |
|---|---|---|---|---|
| M3 | discussion | tweedledee, tweedledum | `[[td, tdm]]` | 1 team × 2 members |
| M4 | clarify | alice, hatter, td, tdm | `[[a, h], [td, tdm]]` | 2 teams × 2 members each |
| M4 | red-tests | alice, hatter, td, tdm | `[[a, h], [td, tdm]]` | 2 teams × 2 members each |
| M5 | implement | tweedledee, tweedledum | `[[td, tdm]]` | 1 team × 2 members |
| M6 | review | caterpillar, td, tdm | `[[cat], [td, tdm]]` | 2 teams (1 solo + 1 pair) |
| M6 | defend | caterpillar, td, tdm | `[[cat], [td, tdm]]` | 2 teams (1 solo + 1 pair) |

The orchestrator's inner loop (T64) opens windows for all team members concurrently via `asyncio.gather`; structural cap (rotation budget × team count = bounded total deliberations) preserved. The bet: cut wall-clock by ~half on paired-cast meetings without losing the phase mechanics or §VIII observability.

## Top-level numbers

| Metric | 032 baseline | r35 strict-serial | r36 Teams | r36 vs r35 |
|---|---|---|---|---|
| Total cost | $4.7236 | $7.8794 | **$8.8537** | **+12%** |
| Wall-clock | ~28 min | 76.5 min | **53.3 min** | **−30%** |
| Total LLM calls | 465 | 698 | **811** | +16% |
| Production LOC | 1080 | 3247 | 2198 | −32% |
| Test files | 10 | 23 | 20 | −13% |
| Tests passing cleanly | 35 | 99 (15p + 84xp) | **107 (clean)** | **+8% and shape change** |
| Stories | 7 | 27 | 19 | −30% |
| Test scenarios | ~15 | 58 | 60 | +3% |
| Implementations | ~5 | 12 | 5 | −58% |
| Reviews | ~5 | 20 | 7 | −65% |
| Outcome | complete | complete | complete | — |

**Wall-clock recovery: real and substantial.** −30% on the same workflow shape, same directive, same model. Teams delivered exactly what T64 was designed for.

**Cost direction: inverted from prediction.** I expected Teams to hold or drop cost — parallel work was supposed to amortize per-deliberation overhead. Instead, parallel work *speeds up* budget exhaustion: more agents producing tool-call work concurrently means more cost burned per second of wall-clock. The wall-clock you save shows up in the budget you spend.

## Per-agent telemetry — Tweedles freed up, Hatter compressed, Caterpillar starved

| Agent | r35 calls | r35 cost | r36 calls | r36 cost | Calls Δ |
|---|---|---|---|---|---|
| tweedledum | 195 | $2.36 | **348** | $3.90 | **+78%** |
| tweedledee | 260 | $2.65 | 299 | $3.08 | +15% |
| **mad_hatter** | **176** | $1.89 | **117** | $1.25 | **−34%** |
| caterpillar | 31 | $0.73 | **23** | $0.43 | −26% |
| alice | 17 | $0.12 | 15 | $0.11 | −12% |
| cheshire_cat | 14 | $0.08 | 5 | $0.03 | −64% |
| white_rabbit | 2 | $0.03 | 3 | $0.03 | +50% |
| queen_of_hearts | 3 | $0.02 | 1 | $0.02 | −67% |
| **Total** | **698** | **$7.88** | **811** | **$8.85** | **+16%** |

The signal across non-Tweedle agents is unambiguous: **bound expansion paths got bound harder under Teams.** Hatter, Caterpillar, Cat, Queen all decreased. The structural cap held; team windows didn't loosen any of those compressions.

What changed: **Tweedles ate more of the budget.** Tweedledum nearly doubled (+78%). When their team windows opened concurrently, both Tweedles ran deep tool loops in parallel — `read_file → write_file → run_tests → write_file → run_tests` — and Teams didn't slow either of them down by waiting on the other. The wall-clock you save by running them in parallel reappears as concurrent token consumption.

## Findings

### F1 — Team windows delivered the wall-clock recovery analysis 034 F2 predicted

53.3 minutes vs 76.5 minutes is a 30% reduction on the same directive, same model, same workflow shape. The mechanism is exactly what was hypothesized: paired agents in a team (Tweedles in M3/M5, [Alice + Hatter] and [Tweedles] in M4) deliberate concurrently inside one team window via `asyncio.gather` rather than serially. With 5 per-feature M4 iterations × 2 team windows per iteration × 2-member teams, plus 5 per-feature M5 iterations × 1 team window × 2-member teams, the savings compound.

The gap between r36 (53.3) and 032's pre-phase baseline (28 min) is now ~1.9× rather than r35's ~2.7×. About half the wall-clock penalty has been recovered. The remaining gap is primarily the per-window orchestration overhead (publish window-open, wait for deliberation completion, classify response, emit events) plus the inherent serialization between rotations and between phases.

### F2 — Phases ran out of room before their structural work completed

**M6's defend phase aborted with rot=0 win=0** — zero windows ever opened. The phase events file shows it directly:

```
review.review:  exhausted   rot=2 win=6 acts=(cat:2,td:2,tdm:2)
review.defend:  aborted     rot=0 win=0 acts=()
```

The mechanism: review phase ran its full 6 windows (2 rotations × 3 cast members), consuming most of M6's $1.20 meeting_budget. When defend phase opened, the orchestrator's first action is the budget check at the top of the inner loop. Budget exceeded → phase aborted before any window opened.

Across all phases:

```
Reason distribution: aborted: 10, exhausted: 7, succession: 1
```

**10 of 18 phases aborted via meeting_budget.** Most phased meetings hit budget mid-phase or before a phase could open.

This is structural work left on the table — not a cost problem. r36 only has 7 reviews because Caterpillar got her 2 review-phase deliberations (good) but her findings were never addressed: Tweedles never got their defend-phase windows. The TDD red→green→fix-on-review loop was truncated at "fix-on-review." That's quality output we *would* have shipped if defend had run.

The right fix isn't to make runs cheaper; it's to **let phases run to their structural completion**. The whole P9 thesis is that phases give us a *structural* unit (deliberations bounded by rotation cap × cast size) for measuring work — dollars are an artifact of how the underlying API is priced. Letting dollars override the structural unit was a design call from T58 that turns out to be backwards: we should let phases finish their declared rotations, with dollars as an outer safety-net cap that fires only on catastrophic divergence.

Three implementation paths:

1. **Per-phase budgets**: each phase declares its own dollar cap. M6 review and defend get separate $0.60 budgets each instead of sharing $1.20. Solves M6 directly but cosmetic — the same contradiction recurs at the per-phase level when Teams burns budget faster.
2. **Decouple structural cap from dollar cap**: gate meeting_budget at `_run_one_meeting` (between meetings) rather than inside `run_phased_meeting`'s inner loop. Phases run to rotation cap / succession / exit_condition; the dollar cap fires between phases or between meetings. **The thesis-aligned fix.**
3. **Adaptive rotation budgets**: when meeting cost is at 80% of cap, halve remaining phases' `max_rotations`. Hybrid approach.

I lean **option 2**. The P9 design call was "phases bound deliberations, deliberations are the load-bearing unit"; option 2 makes that statement consistent. Cost stays a function of how much structural work the run does, not a separate gate that overrides the structure. A run that produces double the test coverage takes double the budget — that's the right accounting.

### F3 — Output quality went up qualitatively, even with less volume

The numbers say less of everything except tests. But the *shape* of what's there is better than r35:

- **Pure Python architecture, layered cleanly.** r36 ships 7 Python modules: `models.py` (87 LOC, dataclass-based session/settings/aggregate schema), `store.py` (265 LOC, persistence layer), `api.py` (344 LOC, endpoints), `client.py` (480 LOC, frontend integration), `ui.py` (538 LOC, view layer), `session_start_widget.py` (483 LOC, focused component), `__init__.py` (1 LOC). MVC-ish layering with explicit boundaries. r35 by contrast shipped Python "shadow" implementations of TypeScript modules so pytest could test contracts in isolation — clever but architecturally ugly.
- **107 cleanly-passing tests** vs r35's 99 effective green. The "effective green" in r35 included 84 tests that were marked `pytest.xfail` in M4 (red), turned green by M5's implementation, but Tweedles never stripped the xfail decorators. Cosmetic, but it meant r35's test suite output was full of `XPASS` markers that look like warnings. r36's test suite is just clean passes — 107 tests, 62 skipped (deferred features), 1 xfailed (genuine still-broken). Much cleaner state to ship from.
- **Broader feature coverage.** r35 went deep on features 1-2 (quick_start_timer, configurable_intervals) — 9 test files for quick_start alone. r36 covered all 5 features with 4-5 test files each. Different strategy: r35 was depth-first per feature, r36 was breadth-first across the whole product.
- **ADR-001 framed differently.** r35 made the load-bearing call about "settings sync architecture" (single-device vs cloud). r36 made the load-bearing call about "session lifecycle and persistence" (immutable session log + mutable settings + computed daily aggregate). The latter framing produced a cleaner schema-first design; the former produced a deployment-first design that dragged the rest of the team into polyglot territory.

Why did the architectural framing differ? Possibly because in r35 (strict serial), Cheshire Cat had 14 calls vs r36's 5 — Cat's role is the architectural deliberator. In r35, Cat had more space to surface the deployment-architecture concern; in r36, with Cat compressed (-64% on calls), the architecture conversation went cleaner to a data-model framing. **Teams indirectly compressed architectural sprawl by giving Cat fewer windows to expand into deployment-level concerns.** Speculative, but consistent with the pattern.

### F4 — Phase-event persistence (T58d) finally lets us measure deliberations directly

This is the analysis 034 F6 fix paying off. Phase events are now on disk (191 lines of JSONL in `r36/.wonderland/phase-events.jsonl`), and the §VIII observability primitives are measurable post-run.

**Per-agent deliberations** (the unit phases bound, finally measurable):

| Agent | Acts | Passes | Total deliberations |
|---|---|---|---|
| tweedledee | 19 | 4 | 23 |
| tweedledum | 20 | 3 | 23 |
| alice | 8 | 1 | 9 |
| **mad_hatter** | **7** | **2** | **9** |
| caterpillar | 2 | 0 | 2 |

**Hatter shipped 9 deliberations across the entire run.** That's the load-bearing number. His 117 LLM calls were the *expansion of those 9 deliberations into tool loops* — read_file, write_file, run_tests, retry. The structural cap (1 clarify + 3 red-tests = up to 4 windows per M4 iteration × 5 iterations = 20 max, fewer if budget aborts) was enforced. 9 actual deliberations means budget aborts cut off a meaningful chunk of his structural cap.

The headline metric in T59 was "Hatter call count drops without test quality dropping." That metric was the wrong unit; it tracks tool-call expansion, not deliberation count. **The right metric — Hatter's deliberation count, now measurable — confirms phases compress sprawl as designed.** 9 deliberations across 5 features × 2 phases × 2-rotation-cap is meaningfully bounded. In legacy (032), Hatter's deliberation count was unmeasurable but inferred from 65 calls in unbounded windows.

**Pass rate: 15.2% (10 passes / 66 total deliberations).** That's the §VIII baseline. Specific patterns worth noting:
- **Caterpillar: 0 passes.** Categorical force shape — when she had a window, she always acted. Her constitutional role doesn't naturally pass; she reviews until done.
- **Hatter: 2 passes (22%).** Compressed to bounded act-or-pass; some scenario surfaces ran out of fresh failure modes by his second window.
- **Tweedles: 4 + 3 = 7 passes across 46 deliberations (15%).** They mostly act when given a window — the implementation iterate-red-green loop has obvious next steps until the feature is green.
- **Alice: 1 pass.** Her grounding role naturally fires only when something needs grounding; mostly she had something to add per window.

These are the §VIII fingerprints we can finally see post-run. Future analyses can correlate pass rate with constitution to validate that each character's failure-mode profile matches their measured behavior.

### F5 — Phase end reason distribution exposes the budget pressure

```
exhausted (rotation cap reached): 7 phases
aborted (meeting_budget hit):     10 phases
succession (all-pass, natural):    1 phase
exit_condition (artifact ship):    0 phases
```

**Only one phase ended via succession.** The model where agents pass in succession when there's nothing more to add isn't matching observed behavior — agents almost always have something to act on when given a window. This is partly because tdd-serial-phased's per-feature M4/M5 iterations are tightly scoped (one feature's surface to cover), so agents are rarely in a state where they'd pass.

**Exit condition fired zero times.** None of the phases declared an `exit_condition_artifact` in this workflow. That's a dimension we haven't exercised — worth setting up for an M3 phase where "the contract has shipped" could end the phase early.

**Half the phases aborted on budget.** Per F2, this is the substrate contradiction. The right fix isn't to raise budgets across the board — it's to decouple structural cap from dollar cap.

### F7 — Global budget cap isn't enforced on phased runs (substrate bug)

r36 declared `budget_dollars = 5.00` at runner setup and finished at $8.85 — 77% over the cap. r35 was 58% over the same $5 cap. This isn't variance or run-cost-reflects-quality; it's a substrate gap.

The mechanism: in the legacy `_convene_one` path, `runner.budget_dollars` is enforced by the runner's background watcher emitting a `RunnerEvent(kind="budget_exceeded")`, which `_convene_one` catches in its `runner.events()` drain loop and sets outcome to `GLOBAL_BUDGET`. But `run_phased_meeting` (the new path) doesn't drain `runner.events()` — it owns deliberation directly via `compose_context + deliberate`. So `budget_exceeded` events are emitted but never observed. The phased orchestrator only knows about the per-meeting budget (via `runner.total_cost - cost_before >= meeting.meeting_budget`), not the global one.

The fix is small: check `runner.total_cost >= runner.budget_dollars` (or the cached `runner._budget_exceeded` flag) at the top of the phased inner loop, set `outcome = "GLOBAL_BUDGET"`, break out and propagate. ~10 LOC of plumbing.

This is independent of the F2 contradiction. F2 says "let phases finish their structural work without meeting_budget cutting them off." F7 says "but DO respect the operator's declared global cap." Both can land together — phases run to structural completion within their meeting budget, but the run aborts when global budget is hit. Operators who declare $5 should be able to trust that's the ceiling.

### F6 — Output drift took a different shape than r35

r35's accessibility coverage was explicit deaf-user representation (Story-024 Priya, persona = "deaf software engineer"). r36's accessibility ground was different: **voice input** (Scenario-034: "custom-duration voice input accessibility"; Scenario-041: "user with voice input enabled activates microphone"). Both runs derived accessibility from constitutional grounding without the directive asking for it (analysis 034 F5's thesis), but each run picked a different accessibility angle to cover.

Whether this is a phase-mode side effect (different team configurations surface different concerns) or random variance is unknowable from N=2. Worth tracking — if r37+ continue producing accessibility coverage but in *different* shapes each time, that's a signal that constitutional grounding produces "accessibility somewhere" reliably but the specific axis is path-dependent.

## What this analysis doesn't show

- **N=2.** r35 vs r36 is two runs against one directive. Pomodoro variance has been substantial historically (032's $4.72 to r35's $7.88 to r36's $8.85). The 30% wall-clock recovery is large enough to read as Teams-effect rather than variance, but the cost direction (+12%) is small enough that variance can't be ruled out.
- **The substrate contradiction is structural, not measured.** F2's analysis of why M6 defend aborted is from inspecting the phase event log; we haven't measured *how much* of total cost overrun is attributable to the budget-vs-structural-cap tension vs other factors.
- **Output-quality comparisons are subjective.** "Cleaner architecture," "broader coverage," "better-shaped tests" are read-it-yourself impressions. The hard numbers (107 vs 99 passing tests) capture some of it; the structural call (pure Python vs polyglot) is a reading I made on the artifacts.
- **The deliberation-count metric is new.** T58d shipped phase events to disk for r36; r35 had them only on the live wire. So we can measure r36's deliberation count but only infer r35's. The "Hatter compressed to 9" finding is meaningful in absolute terms but not directly comparable to r35.

## What's next

In priority order. Operator's stated preference: quality > cost; budget cap respect is a real bug but can land later, not blocking on the next quality round.

1. **First exit_condition_artifact deployment.** F5 noted zero phases used this. M3's `discussion` phase is a natural fit: end the phase when a `contract_note` of state=agreed ships. Future analyses get a fourth phase-end reason to interpret. Cheap workflow YAML edit; lands with the next phased run.

2. **Re-run pomodoro on tdd-serial-phased.** A/B against r36 to validate the wall-clock + quality findings hold across N=3 vs N=2. Same workflow, same directive. Watch: does the 30% wall-clock recovery vs r35 reproduce? Does quality stay up (107+ cleanly passing tests, layered architecture, broader feature coverage)? Does Hatter stay compressed (~9-10 deliberations)?

3. **Begin tracking pass-rate-by-character across runs.** F4's per-agent deliberation map is a §VIII fingerprint. After 3-5 runs we'll see whether each character's pass rate is stable (= constitutional fingerprint) or run-dependent (= context-driven). Either is informative. Build a tiny `daedalus pass-rates` CLI command that aggregates across `.wonderland/phase-events.jsonl` files in any directory tree.

4. **Decouple meeting_budget from phase mechanics** (F2 fix). Phases should run to structural completion (rotation cap / succession / exit_condition). Meeting_budget moves to `_run_one_meeting` as a between-meetings check, not inside the phased inner loop. M6 defend gets to run; review findings get addressed. Lands when we want to close the truncated-phase gap; not blocking immediate quality work.

5. **Wire global budget gate into the phased orchestrator** (F7 fix). The bug analysis 035 surfaced: `runner.budget_dollars` (the operator-declared cap) is enforced via `runner.events()` in the legacy `_convene_one` path, but `run_phased_meeting` never drains runner events — it owns deliberation directly. So `budget_exceeded` never reaches the phased loop, and runs blow past the declared cap (r36 hit 177% over $5). Fix: check `runner.total_cost >= runner.budget_dollars` (or `runner._budget_exceeded`) at the top of the phased inner loop, set `outcome = "GLOBAL_BUDGET"` and break out. Quality runs are fine without it; operators who want a hard ceiling need it.

6. **Don't yet ship team windows in tdd or canonical.** P9.5 validated against tdd-serial-phased; the wall-clock recovery + quality wins are real. Hold rollout to other workflows until #4 + #5 land — the truncation patterns we saw in M6 defend would surface differently in canonical's M5 and tdd's parallel M4.

## Headline

**Team windows produced qualitatively cleaner output across every dimension that matters: 107 cleanly-passing tests (vs r35's 99 mixed-shape effective green), pure-Python layered MVC architecture, broader test coverage, more focused stories. Wall-clock recovery (−30% vs r35) landed as predicted. The §VIII observability primitives are finally measurable thanks to T58d phase events on disk — Hatter shipped 9 deliberations across the entire run, confirming the structural cap was real all along; "Hatter calls" was the wrong unit to measure.** Cost rose 12% — directionally fine when output quality is up proportionally. The substrate gaps that surfaced (10 of 18 phases truncated by meeting_budget mid-flight; global runner.budget_dollars cap not enforced on phased runs at all) are real but not blocking the next round of quality work — the operator's stated preference is quality first, budget-respect-as-substrate-bug to land later. With those fixes (F2 + F7), the phased substrate becomes the right default for productivity-shaped directives. Without them, the substrate works but operators have to babysit the global budget.
