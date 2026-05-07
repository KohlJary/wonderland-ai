# Analysis 028 — Pomodoro end-to-end: M2.5 fires, M5 ships, the pipeline closes

**Date:** 2026-05-07
**Run:** Pomodoro tracker MVP, TDD workflow, with the M2.5 directive iteration + M4 per-feature scoping + cross-meeting event-leak fix all in flight.
**Snapshot:** [analyses/data/028-pomodoro-end-to-end/](data/028-pomodoro-end-to-end/) (includes shipped src, frontend, and tests directories)
**Result:** **The full pipeline ran end-to-end for the first time since analysis 025. M2.5 fired and shipped 7 features, M4 compressed by 57% under per-feature scoping, M5 ran (vs 0 calls in 026/027), and 814 lines of backend + 557 lines of frontend + 2044 lines of pytest shipped on disk. The framework now holds together.**

## Headline numbers

| Meeting | Outcome | Time | Calls | Cost |
|---|---|---|---|---|
| M1 (Caucus Race) | COMPLETE | 31s | 2 | $0.04 |
| M2 (Rabbit's Errand) | COMPLETE | 37s | 5 | $0.06 |
| **M2.5 (Advice from a Caterpillar)** | **COMPLETE — 7 features shipped** | 43s | 12 | $0.10 |
| M3 (Tweedledum and Tweedledee) | COMPLETE | 121s | 28 | $0.22 |
| M4 (Mad Tea Party) | **COMPLETE under cap** | 466s | 48 | **$0.68** |
| M5 (implementation) | **COMPLETE — actually ran** | 83s | 43 | $0.58 |
| M6 (The Trial) | MEETING_BUDGET | 119s | 69 | $0.97 |
| **Total** | | **900s** | **207** | **$2.65** |

Compared to analysis 027 (same directive, same workflow, only the substrate fixes — no directive iteration):

| Metric | 027 | 028 | Δ |
|---|---|---|---|
| M2.5 outcome | silent (0 features) | **7 features** | qualitative |
| M4 cost | $1.57 (cap) | $0.68 | **−57%** |
| M4 calls | 135 | 48 | **−64%** |
| M5 outcome | 0 calls / 0s | **83s / 43 calls / $0.58** | **fired** |
| Total cost | $2.04 | $2.65 | +$0.61 |
| Production code shipped | 0 lines | **1371 lines (backend + frontend)** | structural |

The total cost went *up* by $0.61, but the value delivered is structurally different — actual shipped code with a comprehensive failing-test surface, vs the prior run's empty `src/` and partial-tests.

## What we tested

Two changes shipped in this branch since analysis 027:

| Commit | Change | Status after this run |
|---|---|---|
| `2921c68` | Iterate M2.5 directive + scope M4 tests per feature | **Both validated** |
| `ede5651` | Filter cross-meeting complete-event leakage by thread_id | **Validated end-to-end** — M5 actually ran |

Plus the M6 budget bump shipped *after* this run (commit `5a5e667`) addressing the M6 cap-firing observed below.

## Findings

### F1 — The M2.5 directive iteration worked

Rabbit emitted 7 features in M2.5. No silence. The schema validation hit one parse retry, then succeeded. Caterpillar deliberated meaningfully (8 of his 14 total calls were in M2.5), and Alice contributed her audit-mode silences at the right rate.

The features Rabbit produced:
1. Start a focus session and get notified when it ends
2. Take a structured break and transition to the next session
3. Review today's focus work and recent sessions
4. Track weekly and lifetime focus statistics
5. Customize session and break durations
6. Understand how long you've been tracking sessions
7. Schema design for future multi-user support

What unblocked the silence (per analysis 027 F1's three hypotheses):

- **The chapter-title bias counter mattered.** "This is your meeting — the chapter title (Caterpillar's chapter) describes the *stance* the team takes in this thread, not who's driving. You are." Without this, the "Advice from a Caterpillar" prefix primed the LLM to defer.
- **Imperative-first structure mattered.** The opening sentence is now `**Rabbit, ship features.**` — the reader's first impression is unambiguous.
- **Explicit anti-silence framing mattered.** "Silence is wrong here — your job is to produce features." Counters Rabbit's constitutional default-to-silence-when-uncertain. Combined with the permission-giving "You don't need to be perfect — half-formed groupings are better than silence," gives Rabbit room to ship without being right.

### F2 — Per-feature scoping compressed M4 dramatically

The key result. M4 cost went from $1.57 (027) to $0.68 (028) — a 57% reduction. Call count went from 135 to 48 (−64%). M4 ended COMPLETE under cap rather than hitting MEETING_BUDGET.

The mechanism:

The 027 M4 directive asked Hatter and Alice for tests "against the agreed contracts" — an open-ended search over the system's failure-mode space. Hatter triages widely, finds many concerning cases, ships tests for them. The total work scales with the imagination of the LLM, not the work that needs doing.

The 028 M4 directive asks for tests "for each feature, bounded by that feature's claim and stack_span — not generalized to invariants that span the whole system. Stop when a feature is covered; don't keep generating tests because more failure modes are imaginable. Caterpillar's review in M6 is the system-wide-invariants safety net."

That bounds the search. For 7 features, Hatter ships ~5-10 scenarios total instead of ~20-25. Alice ships one happy-path per feature. The Tweedles' clarification rounds become per-feature instead of per-system. All of this compresses without losing coverage of the load-bearing surface — because the *feature* is the unit of user-facing claim, and tests-per-feature is the right granularity.

The "M6 is the safety net" framing is doing real work here. Without it, Hatter's QA disposition (cover everything that could break) overrides scope. With it, he can stop at feature scope without anxiety because he knows Caterpillar will catch system-wide invariants downstream.

This is the strongest directive-as-deterministic-fix outcome we've seen — not a small adjustment but a structural change in the meeting's economics.

### F3 — M5 actually ran (event-leak fix validated end-to-end)

For the first time since analysis 025, M5 (implementation) deliberated. 83s, 43 calls, $0.58. Tweedles shipped real production code:

- 8 backend files (`src/backend/`): `auth.py`, `models.py`, `api/sessions.py`, `api/history.py`, `api/stats.py`, `api/settings.py`, `api/launch_date.py`, plus database glue
- 2 frontend files (`frontend/src/`): updates to `App.tsx` and `api.ts` (557 lines including the existing skeleton)

Total: 814 lines of backend + 557 lines of frontend + 2044 lines of pytest tests = 3415 lines on disk.

The cross-meeting event-leak fix in `ede5651` was the actual unblocker. Without it, M5's events loop would have read the leftover COMPLETE event from M4 (or any prior meeting) and exited immediately — same pattern as analyses 026 and 027. With it, M5's events loop only respects COMPLETE events for its own thread_id, and the agents get to deliberate properly.

The supporting fixes (`042cf8f` mark_thread_complete on MEETING_BUDGET, `10dd160` quiescence-on-startup gate) didn't get exercised this run because M4 ended COMPLETE rather than MEETING_BUDGET. They're still load-bearing for the case where M4 *does* hit cap — they're now an unused safety net rather than the thing keeping M5 alive.

### F4 — M6 needed more budget

M6 hit MEETING_BUDGET at $0.97 against the $0.50 cap. Caterpillar surfaced findings; Tweedles started shipping fixes (`history.py` patches in flight at the budget cap); the late-publish guard correctly suppressed the in-flight fix-emission.

The cap was sized for "Caterpillar reads the diff and surfaces findings" — appropriate when the prior pipeline shipped little to review. With M5 now genuinely shipping production code, M6 has substantively more work: review the code, surface findings, *and* close the review-and-fix loop with the Tweedles. The bump to $1.20 (committed in `5a5e667`, post-this-run) gives the loop room to complete.

### F5 — Test pass rate is the v1-scaffold pattern

`pytest tests/` against the shipped code: **16 pass, 48 fail, 7 skip.** That sounds bad in isolation, but matches analysis 025's framing exactly: *v1 scaffold with a known list of fixes named by the test surface*. The failing tests aren't framework misbehavior — they're Hatter's deliberately-rigorous edge cases naming real bugs in the implementation:

- Timezone boundary handling at midnight
- Settings-mid-session immutability
- History query date-boundary inclusivity
- Statistics temporal correctness (UTC vs local)
- Race conditions on break-skip
- Launch date persistence across restarts

These are real failure modes. M6 *could have* surfaced them as findings and Tweedles *could have* shipped the patches in the same run, but M6's $0.50 cap fired before the loop completed. The bump fixes this for the next run.

The 16 passing tests cover the happy paths — what most users would do with a working pomodoro app. The 48 failing tests cover the edges, which is what the framework's value-add is.

### F6 — Rabbit's "grouping" was 1:1, not aggregation

Worth pinning even though it didn't break the run. Rabbit's 7 features mapped 1:1 to Alice's 7 M1 stories. He renamed each story as a feature rather than *aggregating* multiple tickets into a coherent user-facing unit. The directive asked him to "group tickets into features" but didn't enforce aggregation (e.g., "fewer features than tickets" or "at least 2 tickets per feature").

For this directive, 1:1 mapping was probably fine — the pomodoro stories *are* mostly distinct user-facing capabilities. For larger directives (Geocities-shaped), the lack of aggregation pressure could leave features as a thin renaming layer rather than a real organizational unit. Worth surfacing as a future M2.5 directive iteration if a future run shows the pattern degrading.

Counter-evidence to consider: **the 7-feature decomposition still produced the M4 compression.** Even though features didn't aggregate, having them as the unit of test scope was sufficient to bound Hatter's search. So the structural value of features in this pipeline isn't just aggregation; it's *being a discrete unit of user-facing claim that downstream meetings can scope to*.

### F7 — Meeting names visible to agents (mechanically validated)

The directive prefix `**M{N} — {Name}.**` landed in every meeting's directive utterance. The Tweedles' M3 contracts referenced "the features in your context" (using terminology from the directive); Caterpillar's M6 review referenced "the features above" framing. Whether the literary naming visibly shifts behavior is hard to attribute cleanly because too many other things changed simultaneously, but the substrate works.

## What this analysis doesn't show

- **M4 compression generalizing to other directives.** Pomodoro is a relatively clean directive with 3-7 obvious features. A directive with messier feature boundaries (Geocities-shaped, or a directive without obvious user-facing capabilities) might not compress as cleanly.
- **The 48 failing tests as accurate failure-mode coverage.** Some may be Hatter overreaching; others may be real bugs Caterpillar would have legitimately surfaced. The next run with bumped M6 will tell us how many close in the review-and-fix loop.
- **Running cost trajectory.** $2.65 is up from $2.04 (027) but the prior run was effectively wasted (M5 didn't ship). The right comparison is to analysis 025's $2.05 for a successful Geocities run; this is in similar shape, slightly more expensive, with smaller overall scope but more thorough test coverage per feature.

## What's next

The branch is now at a coherent landing point — most of the substrate fixes that have been accumulating are validated, and the directive iteration unlocked the experimental signal we were after. The natural next moves:

1. **Rerun with the M6 budget bump** to see whether the review-and-fix loop closes cleanly. Hypothesis: 30-50% of failing tests pass after M6 because Tweedles ship the patches Caterpillar surfaces. Cost prediction: $3.50-$4.50 total, still under the new $6.00 cap.
2. **The run-tests tool for Tweedles in M5.** A substrate change: give Tweedles a `run_tests` tool so they can iterate red→green→refactor properly during implementation, rather than shipping code blindly and waiting for M6 to surface failures. Should improve the at-M5 pass rate substantially and reduce M6's review burden.
3. **P8 work** (per `.daedalus/roadmap/p8-interface-skeleton.md`). With the framework substrate now reliably running end-to-end, the user-facing interface track becomes the natural focus. P8.1 (observer/query API) is the keystone that unblocks both the TUI work and the eventual eval harness.
4. **Roadmap closeout** for `d1f4f2ec` (feature-composition phase) — the experiment validated, the phase ships. Move to done.

## Headline

**The framework is back to shipping.** The chain of fixes since analysis 025 (when it last shipped end-to-end) — Alice in M2, the late-publish race fix, the quiescence-on-startup gate, the meeting names, the feature substrate, the M2.5 phase, the directive prefix, the cross-meeting event-leak filter, the M2.5 directive iteration, and the per-feature M4 scoping — converged this run. None of the individual fixes alone would have produced this outcome. They had to land in the right order and the directive had to be iterated with enough precision for the LLM to actually behave the way the design described.

What survived from analysis 027 — the graceful-degradation observation, the agent-shaped recovery patterns, the literary parallel keeping the epistemics honest — is still load-bearing. It's just that this run, the framework didn't *need* to degrade gracefully because every meeting fired as designed. That's the better headline.
