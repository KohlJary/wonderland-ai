# Analysis 029 — Substrate convergence after four-run iteration

**Date:** 2026-05-08
**Run sequence:** Pomodoro v3 → v4 → v5 → v6, all on the same directive, same workflow (TDD), same skeleton (fullstack-fastapi-react).
**Snapshots:** [analyses/data/029-substrate-convergence/](data/029-substrate-convergence/) — full `.wonderland/` and `run.log` for each of the four runs.
**Result:** **The framework's substrate is now structurally correct end-to-end. After analysis 028's banner, four sequential runs each surfaced one substrate bug, each fix shipped, and v6 lands as the new banner with real test signal (29 pass / 65 fail / 13 skip — v1 scaffold + named bug list pattern from 025/028). The cost climbed ($2.65 → $4.24), and Hatter's scope-creep is the next leverage point.**

## The iteration arc

Four runs against the same directive. Each surfaced a different substrate failure mode. Each fix shipped before the next run.

| Run | Outcome | Headline | Fix shipped |
|---|---|---|---|
| **v3** | Mid-pipeline failure | Wall-clock global timeout fired during M4, cascaded into M5 RUNNING outcome | Removed runner-level wall-clock timeout (`b9d4402`); ThreadMonitor's quiescence-fallback kept |
| **v4** | M5 ran but tests broken | Skeleton-overwrite half-replacement: Tweedles removed `HelloMessage` but left `messages.py` importing it → pytest collection failure → no test signal | TEMPLATE markers in skeleton + `BUILD FAILURE` detection in `run_tests` + M5 directive update (`7c53399`) |
| **v5** | M5 RUNNING again (different cause) | The `ede5651` cross-meeting filter was symptomatic, not structural — the real bug was in `Runner.events()` auto-returning on any `complete` event regardless of thread_id | Producer-layer filter via `terminal_thread_id` parameter on `events()` (`f15bab5`) |
| **v6** | **Substrate banner** | All meetings ran; M5 deliberated cleanly post-MEETING_BUDGET; skeleton overwrite done correctly; pytest collected and ran 107 tests | (none — v6 ran on the cumulative substrate fixes) |

## Per-run quantitative summary

| Metric | v3 | v4 | v5 | v6 |
|---|---|---|---|---|
| Total cost | $2.97 | $2.36 | $3.44 | **$4.24** |
| Total wall clock | 1427s | 762s | 929s | 1520s |
| Total LLM calls | 239 | 232 | 207 | 335 |
| M2.5 features shipped | 4 | 6 | 4 | 6 |
| M2.5 aggregation ratio | 4/9=0.44 | 6/9=0.67 | 4/9=0.44 | 6/6=1.0 |
| M4 outcome | TIMEOUT | COMPLETE | MEETING_BUDGET | MEETING_BUDGET |
| M4 cost | $1.13 | **$0.47** | $1.71 | $1.72 |
| M5 outcome | RUNNING (broken) | COMPLETE | RUNNING (broken) | **COMPLETE** |
| M5 calls | 0 | 43 | 0 | 37 |
| M6 outcome | MEETING_BUDGET | MEETING_BUDGET | MEETING_BUDGET | MEETING_BUDGET |
| Tests collected | broken (Import) | broken (Import) | broken (Import) | **107** |
| Tests passing | n/a | n/a | n/a | **29** |
| Tests failing (real) | n/a | n/a | n/a | 65 |

The crossing point is v6: the first run since 025 where the framework shipped real production code AND real test signal. v4 came close (M5 ran, code shipped) but the half-overwrite hid all test output behind a collection error.

## Substrate findings (the bug class lessons)

### F1 — Wall-clock semantics are a category error in turn-based deliberation

v3's M5 ended with outcome=`RUNNING` (the workflow's initial placeholder, never updated to a terminal state). Tracing it: the runner's `_enforce_timeout` task fired at the global 1200s wall-clock cap *during* M4, generated a `timeout` RunnerEvent, M4's events loop consumed it and set outcome=TIMEOUT, M5's events loop started but had no events to consume (the timeout task had exhausted), and the loop hung until M5 was cleaned up via cancellation, leaving outcome at `RUNNING`.

The framework's `feedback_no_wall_clock_in_turn_based` memory had been right all along: "Wonderland is turn-based; timers are category errors. Wall-clock as safety net only." We had three wall-clock mechanisms running; only one was harming. The fix was deletion: removing the runner-level timeout entirely. ThreadMonitor's wall-clock quiescence-fallback (300s) was kept because it's already explicitly framed as the safety net for hung deliberation. Tool subprocess timeouts (60s for `run_tests`, 10s for git) were kept because they're transport-layer, not deliberation-layer.

The lesson: when an existing safety mechanism only ever fires unhelpfully and protects against nothing the budget doesn't already protect against, it's not a safety net — it's a bug factory.

### F2 — Half-replacement breaks the import chain

v4 was a structural success that hid behind a v1-scaffold output failure. Tweedles replaced `models.py`'s `HelloMessage` class with their pomodoro `FocusSession` and `Config`, but left `api/messages.py` importing `HelloMessage`. The cascade: `api/__init__.py` imports `messages.py`, `messages.py` imports `HelloMessage`, conftest imports the API, pytest collection fails on ImportError, all test signal disappears.

The Tweedles thought they were "extending the tree" (per the M5 directive) by writing `models.py` with the right content. They were respecting the file-path rule but violating semantic invariants — the file existed, but the symbols expected by the rest of the codebase were gone.

The fix was three-layered:
- **Skeleton**: TEMPLATE comment blocks at the top of `models.py`, `api/messages.py`, `api/__init__.py`, and `tests/test_messages.py`, naming exactly which other files need updating if the placeholder is removed
- **Tools**: `run_tests` enhanced to detect collection failures (`ERROR collecting`, `ImportError`, `ModuleNotFoundError`) and lead its result with `BUILD FAILURE` + a pointer to the offending file
- **Directive**: M5's directive now names the TEMPLATE convention explicitly and adds a STOP rule — if `run_tests` reports `BUILD FAILURE`, fix the import chain before any new `write_file`

v6 validates the fix: Tweedledum did the full cleanup correctly. The TEMPLATE markers reached the LLM at read time and gave it the right mental model.

### F3 — Filtering at the consumer is structurally insufficient

v5 surfaced a deeper version of the v4-era cross-meeting event leak. The `ede5651` fix added a thread_id filter inside `workflow.py`'s events loop — when a `complete` event arrived with the wrong thread_id, the workflow would `continue` past it. That looked correct.

But `Runner.events()` is an async generator with a return-on-terminal-event clause:

```python
async def events(self) -> AsyncIterator[RunnerEvent]:
    while True:
        event = await self._event_queue.get()
        yield event
        if event.kind in ("complete", "aborted", "timeout"):
            return
```

The `yield event` happens *before* the `return` check. Sequence:
1. M5's events loop pulls a stale M4 `complete` event from the queue
2. `events()` yields it to the workflow
3. Workflow filters by thread_id, does `continue`
4. Control resumes inside `events()`, hits the `if event.kind in (...)` check, **returns the generator**
5. Workflow's `async for` cleanly exits because the generator returned
6. M5 ends with outcome=`RUNNING` having processed zero of its own events

The consumer-layer filter only delays the inevitable. The filter has to live at the producer layer — `events()` itself has to know which completes count as "this meeting's." Fixed in `f15bab5` with a `terminal_thread_id` parameter.

The lesson, broader than this specific bug: **the workflow's per-meeting events loop is a consumer of an unbounded event stream, but the producer's default contract is "return on terminal event."** Any meeting-level filtering has to happen at the producer side. Patching at the consumer is fixing the symptom, not the cause.

### F4 — The M2.5 aggregation pattern is run-to-run variant

Across the four runs, Rabbit's feature-composition output varied widely:

- v3: 4 features for 9 tickets (0.44 ratio — real aggregation)
- v4: 6 features for 9 tickets (0.67 — partial aggregation, included one architectural-leakage feature "control local-first persistence")
- v5: 4 features for 9 tickets (0.44 — clean aggregation)
- v6: 6 features for 6 tickets (1.0 — back to 1:1 mapping)

v6's 1:1 ratio is interesting because the features themselves *look like real groupings* ("Start and complete a focus session" reads as composed) — but Rabbit produced exactly one ticket per feature. Either (a) the directive's framing led him to compose tickets to match planned features, or (b) the aggregation pressure isn't as forceful as we'd want.

This is variance, not a bug. The directive bounds *direction* (group, name personas, name stack_span) but doesn't enforce a count constraint (≥2 tickets per feature, fewer features than tickets). Adding such a constraint might force more aggregation — but might also push Rabbit into artificial bundling. Worth surfacing as a future iteration if a real-feature run exposes the lack of aggregation as harm.

## Cost trajectory

| Run | Cost | Notable |
|---|---|---|
| 028 (v2) | $2.05 (Geocities tea-party banner) | Pre-this-iteration baseline |
| 028 (v2 pomodoro) | $2.65 | First pomodoro banner |
| 029 v3 | $2.97 | Higher because TIMEOUT wasted M4 work |
| 029 v4 | $2.36 | Lowest cost, but no test signal |
| 029 v5 | $3.44 | Higher; M5 didn't run but M4 sprawled |
| 029 v6 | **$4.24** | Highest. Real test signal, but expensive |

The cost climb v4→v5→v6 is partly substrate-fix-driven (more iteration available means agents iterate more) but partly Hatter's scope-creep into meta-process commentary (F5 below). v6 cost is now ~60% above the v4 banner with comparable end-to-end shipping shape. That's the next leverage point.

## F5 — Hatter is sprawling into meta-process work in M4

Spotted by Kohl across v3-v6. Hatter's late-publish suppressions in M4 are a persistent pattern, but inspecting the actual content reveals it's not the "expected" sprawl (more failure-mode scenarios than the budget can hold) — it's **scope-creep into team-process commentary**.

Looking at v6's Hatter episodic record (12 utterances during M4):

Phase 1 — character-correct work:
- 1 `implementation` (write_file landing test files)
- 1 `test_scenario` shipping 3 scenarios for features 4-6

Phase 2 — scope-creep:
- 3 `concern` utterances *critiquing the workflow process* ("Tweedledee shipped without bus record," "the team's workflow is breaking down")
- 1 `implementation` rewriting contract details ("Contract Ambiguity Surfaced and Fixed: API Path Prefix")
- 1 `concern` self-quoting addressing himself

This is Hatter's §VIII failure mode (scenario sprawl + severity inflation) generalized to **meta-discussion sprawl**. He's leaving his lane (failure-mode scenarios per feature) and stepping into Dodo's lane (team orchestration) and Caterpillar's lane (cross-cutting contract review).

The fix candidate: M4 directive needs to bound Hatter's lane explicitly. Same shape as the Rabbit-shouldn't-be-silent fix from analysis 028 — but inverted: Hatter shouldn't be over-iterating on meta-discussion. Proposed wording:

> *"Stay in your lane — ship failure-mode scenarios for features. If you observe process issues (workflow breaking, contracts ambiguous, other agents going off-spec), raise ONE concern naming the problem and move on. Do not iterate on meta-discussion. Caterpillar reviews shipped work in M6; the Dodo orchestrates the team. Your job is to test."*

This won't land in this commit's analysis but is the natural next iteration.

## What converged in v6

Pulling the substrate findings together: as of v6, the framework structure end-to-end is:

- **M1-M3 clean**: scoping → decomposition → composition → contracts. Costs are bounded, artifacts are produced, late publishes (when they happen) are suppressed cleanly.
- **M4 Tea Party** still hits MEETING_BUDGET reliably, but the budget cap firing no longer cascades into M5. M4's work shipped (test files on disk + test_scenario artifacts) even though the bus emission was suppressed.
- **M5 actually runs** — the events()-level filter holds, regardless of how M4 ended. Tweedles iterate red→green using `run_tests`. The skeleton-overwrite cleanup is correct.
- **M6 closes findings** — Caterpillar's review surfaces real bugs, Tweedles ship fixes, the loop runs until cap. M6 still hits MEETING_BUDGET, suggesting the loop has more work than the cap allows.

The v1-scaffold pattern from analysis 025 holds: 29 passing tests cover the happy paths, 65 failing tests *name* the edges Hatter and Caterpillar caught. A second pass (manual or another framework run) closes the gap. The framework is doing its job — it's the test surface, not the implementation, that's load-bearing.

## What this analysis doesn't show

- **Cost discipline.** $4.24 per pomodoro run is not sustainable as a per-experiment cost when iterating on substrate. The next iteration's job is to bound costs back toward $2.50-3.00 without losing the structural correctness gains.
- **Hatter's sprawl in numbers.** F5 is a qualitative observation. Quantifying it (e.g., percentage of Hatter's M4 utterances that are meta-discussion vs scenario-shipping) would let us track whether the directive fix actually compresses it.
- **Frontend output.** Across all four runs, the frontend half of the cross-stack ratio stayed weak (0-2 files vs backend's 4-8). The per-feature stack_span work in M3 is identifying full-stack features but Tweedledee's M5 implementation isn't matching backend depth. Worth a separate finding once Hatter's bound.
- **N=4, one directive.** Pomodoro is a small-feature directive. Larger directives (Geocities-shaped) might surface different failure modes. The substrate fixes here address pomodoro's failure mode profile; not yet validated against a different shape.

## What's next

Three candidate moves, ranked:

1. **Bound Hatter's lane in M4 directive** (F5's fix). Single content-only edit; should compress M4 cost and reduce late-publish accumulation. Same shape as previous successful directive iterations (`56c3b16`, M2.5 directive).
2. **Bound Tweedles' run_tests iteration loop** so they don't infinitely refine. Hard to measure without instrumentation, so defer until F5's fix surfaces whether Tweedles are also over-iterating.
3. **Frontend stack-span discipline.** Tweedledee's M5 frontend output is consistently weaker than Tweedledum's backend. Could be a directive issue (M5 doesn't differentiate between Tweedles by stack-span) or a constitutional one (Tweedledee's character file underspecifies frontend depth). Worth a focused check before another big iteration.

## Headline

**The substrate is structurally correct.** Four sequential bugs surfaced and fixed across four runs, ending with the framework reliably shipping production code, runnable tests, and review findings end-to-end. None of the individual fixes alone would have produced this — they had to compose, in order, with the directive iterations from analysis 028's M2.5 work as the precondition. The literary parallel keeps earning its keep, but the actual win this iteration was *systems-level*: closing the cross-meeting boundary as a coherent abstraction so each meeting's events loop knows when it's done and when to ignore stale signal from its predecessors.

What's next is *behavioral* tightening (Hatter's sprawl, Tweedledee's frontend), not structural. That's a meaningful shift in where the hard problems live.
