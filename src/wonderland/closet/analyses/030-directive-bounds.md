# Analysis 030 — Selective directive bounds: which compress M4, which backfire, which earn keep

**Date:** 2026-05-08
**Run pair:** Pomodoro v7 (three directive bounds in flight) → v8 (selective revert).
**Snapshots:** [analyses/data/030-directive-bounds/v7/](data/030-directive-bounds/v7/), [v8/](data/030-directive-bounds/v8/).
**Result:** **The substrate is fully converged from analysis 029; this iteration was *behavioral* — adding three directive bounds in v7, observing per-meeting cost shifts, then selectively reverting based on which bounds earned their keep. v8 lands as a banner: $3.56 total (down 16% from v6/v7), M4 COMPLETE under cap for the first time since v4, Hatter calls cut 33%, 5 frontend files (best cross-stack output yet), and 71 useful test outcomes (20 pass / 36 fail / 15 xpassed).**

## What we tested

After analysis 029's substrate convergence, the iteration shifted to behavioral tightening. Three directive bounds shipped in `8a894fd`:

1. **M4 — bound Hatter's lane.** Per 029 F5: Hatter's M4 episodic record showed scenario-sprawl generalizing to meta-discussion sprawl (workflow critique, contract firefighting). Directive added: stay in lane, ship failure-mode scenarios, ONE concern on process issues, no iteration on meta-discussion.

2. **M5 — cap iteration at ~3 cycles per test file.** Hypothesis: Tweedles' run_tests-fueled iteration was eating M5 budget without proportional quality gain. Directive added: stop after 3 cycles, raise concern if still failing.

3. **M6 — distinguish broken bugs from refactor suggestions.** Hypothesis: Tweedles accepting every Caterpillar finding as actionable was the M6 sprawl driver. Directive added: only ship fixes for genuinely broken behavior; push back on refactor suggestions as concerns.

v7 ran with all three. v8 reverted #2 (it backfired), kept #3 (it helped), and tightened #1 (it shifted Hatter's content but not his cost — needed an additional clause).

## Per-meeting comparison across v6 → v7 → v8

| Meeting | v6 (no bounds) | v7 (all 3 bounds) | v8 (selective revert) | v8 vs v6 |
|---|---|---|---|---|
| M1 | $0.07 | $0.04 | $0.03 | −$0.04 |
| M2 | $0.05 | $0.07 | $0.06 | +$0.01 |
| M2.5 | $0.10 | $0.05 | $0.02 | −$0.08 |
| M3 | $0.13 | $0.25 | $0.08 | −$0.05 |
| **M4** | $1.72 cap | $1.73 cap | **$1.22 ✓** | **−$0.50 + COMPLETE** |
| **M5** | $0.38 ✓ | $0.98 ✗ | **$0.53 ✓** | +$0.15 (acceptable) |
| M6 | $1.79 cap | $1.25 cap | $1.61 cap | −$0.18 |
| **Total** | $4.24 | $4.36 | **$3.56** | **−$0.68 (16%)** |

## Per-agent shifts in M4 (the cost-driver meeting)

| Agent | v6 calls/cost | v7 calls/cost | v8 calls/cost |
|---|---|---|---|
| Hatter | 71/$0.96 | 71/$0.99 | **47/$0.50** |
| Tweedledum | 116/$1.43 | 94/$1.15 | 110/$1.26 |
| Tweedledee | 109/$1.30 | 135/$1.76 | 128/$1.27 |

The Hatter cut is structural: his calls dropped 33% (71 → 47) without losing test quality. The "no out-of-lane code shipping" clause added in `7010c74` was the load-bearing piece — v7 had Hatter's calls *unchanged* (71→71) but content shifted from meta-discussion to backend `write_file` calls; v8's tightened bound finally reduced his volume.

## Findings

### F1 — The M5 cycle cap raised the floor

The "~3 cycles per test file is enough" directive raised M5 cost more than it lowered the ceiling. Tweedles read "3 cycles is enough" as "do at least 3" rather than "stop at 3." v6's M5 was $0.38; v7's was $0.98 — 2.5× expansion. Reverted in v8; M5 returned to a healthy $0.53.

The lesson: directives that quantify expected effort tend to *anchor* the LLM rather than *cap* it. The original directive's framing — "iterate red→green using run_tests, fix what's failing" — left the iteration count to emerge naturally from the problem. Adding a number gave the LLM a target to hit.

### F2 — The M6 broken-vs-refactor distinction earned its keep

v6's M6 was $1.79 (49% over its $1.20 cap). v7's M6 was $1.25 (slightly over cap, 30% reduction). v8's M6 was $1.61 (still over, but Caterpillar's review work was substantively richer — 5 reviews vs v7's 3). The bound is doing useful work in compressing speculative-refactor-as-actionable patterns; v8's regression vs v7 isn't the bound failing, it's that more legitimate review work happened.

Keeping the bound. The M6 cap of $1.20 is structurally too tight for "Caterpillar reviews + Tweedles ship fixes" — but bumping the cap further is fighting the symptom. The right next move is probably profiling exactly what burns M6's budget; for now, accept it.

### F3 — Hatter's lane needs *both* meta-discussion AND code-shipping bounds

v7 showed the meta-discussion bound shifted Hatter's *content* (no concerns this run) but didn't change his *call count* (71 → 71). Inspecting his M4 episodic record revealed why: he replaced meta-discussion sprawl with `write_file` calls into `src/backend/`. Same lane violation, different shape.

v8's tighter directive added: "Don't write production code. No write_file calls into src/backend/, frontend/src/, or anywhere outside tests/ and .wonderland/. Production code is M5's job and the Tweedles' lane."

Result: Hatter's calls dropped from 71 → 47 (33% cut). His cost dropped from $0.99 → $0.50. He stayed in the testing lane.

The pattern that surfaces here: **constitutional failure modes don't have a single shape.** Hatter's §VIII is "scenario sprawl + severity inflation" — but in M4 specifically, that sprawl manifests in *whichever direction is unbounded*. Bound meta-discussion, he sprawls into code. Bound code, he sprawls into more scenarios. The directive needs to bound *all* the available expansion paths simultaneously to actually compress his work.

### F4 — Cross-stack output finally landed

Across analyses 026-029-v6, the frontend half of the cross-stack imbalance was the persistent weakness — most runs shipped 0-2 frontend files vs 4-8 backend. v7 broke that open with 4 frontend files (despite test failures). v8 pushed further: **5 frontend files, 4 backend files** — close to balanced for the first time.

This isn't directly attributable to the directive bounds in this commit. The likely cause is the cumulative effect of:
- M2.5's per-feature stack_span surfacing full-stack features explicitly (since 028)
- M3 negotiating contracts per feature with stack_span awareness (since 028)
- M5's run_tests-driven iteration making frontend code visible to verification (since the run_tests addition)
- v7+v8's bounds preventing Hatter and others from absorbing budget that Tweedledee could use for frontend work

Worth tracking: if a future run regresses to backend-only shipping, the cause is one of these chains.

### F5 — Cost trajectory finally bent the right direction

| Run | Total cost | Notable |
|---|---|---|
| 028 (v2 banner) | $2.65 | First end-to-end success |
| 029 v3 | $2.97 | TIMEOUT cascade (substrate bug) |
| 029 v4 | $2.36 | Cheap but tests broken |
| 029 v5 | $3.44 | M5 silent again (different bug) |
| 029 v6 | $4.24 | Substrate banner but expensive |
| 030 v7 | $4.36 | Bounds in, mixed effects |
| **030 v8** | **$3.56** | **Selective revert: banner + cheaper** |

The substrate-correctness story climbed cost (v3-v6: $2.97 → $4.24) because each substrate fix unlocked more iteration potential. The behavioral-bound story now bends the curve back: v8 at $3.56 is 16% cheaper than v6/v7 with comparable or better output quality.

## What this analysis doesn't show

- **N=1 on the new bound.** v8's tightened-Hatter result is one run. Variance across pomodoro runs has been substantial; the result needs at least one rerun to confirm it's the bound and not the dice.
- **The M6 over-cap pattern persists.** $1.61 over $1.20 cap. Either bump the cap (we already bumped from $0.50 → $1.20), or bound Caterpillar's review depth, or accept it as the cost of substantive review.
- **Frontend output may still vary.** 5 files in v8 is best-yet but past runs have varied widely on this axis. Need more data points to know if the 5-file run is the new floor or a happy accident.
- **Pomodoro-shaped only.** All four 029-030 runs were the same directive. The bounds are validated against pomodoro's failure-mode profile; not yet against larger directives.

## What's next

Three things, in order:

1. **Merge `feat/alice-in-m2` to main.** This branch has accumulated 22+ commits since `9a55e71` covering: substrate fixes (race fix, quiescence gate, event-leak filter, wall-clock removal, mark_thread_complete, BUILD FAILURE detection), feature additions (`feature` artifact, M2.5 phase, run_tests tool, meeting names, directive prefix), directive iterations (M2.5 directive, per-feature M4 scoping, M6 budget bump, Hatter/M6 bounds), 5 analyses (026-030), the RUBRIC, and the P8 skeleton. The substrate is in a much stronger place than where this branch started; main should reflect that.

2. **Pivot to P8 (TUI interface).** Per the updated P8 skeleton: build `HistoricalRunHandle` first against `analyses/data/<NNN>/` snapshots — every TUI iteration is free until live mode lands. The substrate iteration loop has been cost-intensive; the TUI track is structurally cost-free until it ships.

3. **The M6 over-cap pattern stays open.** Worth profiling but not blocking.

## Headline

**Three directive bounds shipped, two earned their keep, one backfired and was reverted, one needed a tighter version to actually compress.** The selective revert produced the cheapest end-to-end run since 028 with comparable output quality and the strongest cross-stack output we've seen. The substrate-correctness chapter is closed at v6; the behavioral-tightening chapter is in flight, and v8 is its first banner. Next chapter is the user-facing interface — cost-cheap, morale-load-bearing, and the surface where the framework finally becomes legible to people who don't read source.
