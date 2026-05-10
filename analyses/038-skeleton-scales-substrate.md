# Analysis 038 — Skeleton scales the substrate; per-meeting budget gate is the new ceiling

**Date:** 2026-05-09
**Run:** Pomodoro tdd-serial-phased v5 ([runs/r40-tui-skeleton/](../runs/r40-tui-skeleton/), $10.0005 / $10.00 cap, 47.2 min wall-clock, 10 features (2 near-duplicates → 8 distinct), `fullstack-fastapi-react` skeleton applied via the new T71 picker, completed-with-budget-exceeded escalation).
**Predecessor:** [r39-question-user](../runs/r39-question-user/) — 3 features, $5.12, 36.7 min, 602 LOC production code, no skeleton (analysis 037).
**Result:** **First TUI run to use the T70/T71 skeleton system end-to-end. Shipped 1,243 LOC of working production shape (FastAPI Python backend + React/Vite/TS frontend) on top of the `fullstack-fastapi-react` skeleton — best per-feature efficiency on every axis (cost, wall-clock, LOC-per-dollar) since the substrate began. The skeleton paid back the analysis-037 reframe: when production structure is pre-declared, the team writes into it instead of inventing scattered shapes. But this run also surfaced the next ceiling: the per-meeting budget gate (analysis 035 F2) reproduced — meeting budgets summed past the $10.00 cap and the team STUCK on the main thread, escalating to human review. r40 is the strongest deliverable substrate has produced and the cleanest demonstration that the post-skeleton bottleneck is the budget reconciliation issue, not directive content or model capability.**

## What we tested

Per analysis 037's "What's next" — re-run pomodoro through tdd-serial-phased after the skeleton system landed (T70 bundles, T71 NewRunScreen picker, T73 manifest). Same workflow, same model (`claude-haiku-4-5-20251001`), same `$10.00` budget. The skeleton picker fired automatically because the project root was bare (`is_bare_project_root` from T71); operator selected `fullstack-fastapi-react`; the skeleton's `pyproject.toml`, `src/backend/`, `frontend/`, `tests/conftest.py`, etc. were laid down before M1 convened.

The bet: r39's directive backfill (Guard A — "production code lives in non-test directories") got us from 0 LOC → 602 LOC, but at a 10% per-feature cost premium. With a real skeleton supplying the same structural intent passively, the directive cost should evaporate and per-feature efficiency should improve.

What r40 also surfaced unintentionally: the team double-counted user stories. M2 produced 10 features for what should have been ~8 distinct ones (`feat-002` and `feat-006` both about session-duration sync; `feat-004` and `feat-007` both timer-keepalive). Worth flagging because it implies M2's deduplication or M2.5's composition pass left semantic overlap in the manifest.

## Top-level numbers

| Metric | r36 teams | r38 diff v2 | r39 + Guard A | **r40 + skeleton** |
|---|---|---|---|---|
| Total cost | $8.85 | $7.77 | $5.12 | **$10.00** (cap) |
| Wall-clock | 53.3 min | 49.5 min | 36.7 min | **47.2 min** |
| Features | 5 | 5 | 3 | **10** (8 distinct) |
| **$/feature (raw)** | $1.77 | $1.55 | $1.71 | **$1.00** |
| **$/feature (distinct)** | $1.77 | $1.55 | $1.71 | **$1.25** |
| **min/feature (raw)** | 10.7 | 9.9 | 12.2 | **4.7** |
| **min/feature (distinct)** | 10.7 | 9.9 | 12.2 | **5.9** |
| Total LLM calls | 811 | 690 | 525 | **947** |
| **Production LOC** | 2,198 | 0 | 602 | **1,243** |
| Test files | 20 | 9 | 7 | **21** |
| Test LOC | — | — | — | **6,170** |
| Tool calls | — | ~640 | — | **1,384** |
| Diff tool % | n/a | 55% | 73% (Tweedles) | **45%** |
| Outcome | complete | complete | complete | **complete + budget_exceeded escalation** |

**Per-feature cost dropped 35-42%** vs r38/r39 ($1.55–$1.71 → $1.00–$1.25 depending on whether you count the duplicates). **Per-feature wall-clock halved** (9.9–12.2 → 4.7–5.9 min). The skeleton hypothesis from analysis 037 cashed out at the substrate level: structural intent supplied passively is cheaper than structural intent supplied via convenor directive.

## Per-agent telemetry

| Agent | r39 calls | r39 cost | r40 calls | r40 cost |
|---|---|---|---|---|
| tweedledum | 175 | $1.55 | **346** | **$3.56** |
| tweedledee | 212 | $1.89 | **283** | **$2.70** |
| mad_hatter | 79 | $0.84 | **270** | **$3.42** |
| alice | 12 | $0.07 | 22 | $0.11 |
| cheshire_cat | 9 | $0.06 | 10 | $0.07 |
| caterpillar | 33 | $0.64 | **7** | **$0.06** |
| queen_of_hearts | 3 | $0.03 | 5 | $0.04 |
| white_rabbit | 2 | $0.04 | 4 | $0.04 |
| **Total** | **525** | **$5.12** | **947** | **$10.00** |

Tweedles + Hatter consumed **96.8%** of the budget ($9.68 of $10.00) — extending the r36-onward pattern. Caterpillar is the outlier: **7 calls, $0.06** vs r39's 33 calls, $0.64. Reviews barely happened — consistent with the budget-exceeded outcome (the cap fired before M6 could iterate).

Hatter quadrupled vs r39 (79 → 270), proportional to the feature-count increase (3 → 10) plus the extra surface area from a real fullstack skeleton (test scenarios per feature × frontend + backend test paths). M4 was where most of the new wall-clock went.

## Tool-call profile — navigation-heavy is healthy

| Tool | Calls | % of total |
|---|---|---|
| read_file | 752 | **54%** |
| list_files | 354 | 26% |
| write_file | 72 | 5% |
| str_replace | 60 | 4% |
| grep | 57 | 4% |
| run_tests | 39 | 3% |
| git_status | 32 | 2% |
| git_diff | 18 | 1% |
| **Total** | **1,384** | |

**80% of tool work is *navigation*** (read_file + list_files). r38 ran similar shape but with 0 LOC of production code — the team was reading nothing and writing nothing. r40 has 1,243 LOC of production code on top of a 5-directory skeleton tree, so reads/writes ratio shifts toward reads, which is what you'd expect from a working TDD loop (read tests → read prod → make change → run_tests → repeat).

**Diff tool: 45% adoption (60 str_replace vs 72 write_file)** — down from r39's 73% on Tweedles but still meaningful. The drop is partially mechanical: skeleton-shaped projects start with empty stub files, so first writes have to be `write_file`. The str_replace adoption recovers as iteration deepens.

## Production output shape

```
runs/r40-tui-skeleton/
├── pyproject.toml          (skeleton-supplied)
├── README.md               (skeleton-supplied)
├── src/
│   └── backend/
│       ├── __init__.py
│       ├── main.py         (35 LOC — FastAPI app + router wiring)
│       ├── db.py           (33 LOC — SQLAlchemy session)
│       ├── models.py       (162 LOC — SessionState, Configuration, etc.)
│       └── api/
│           ├── __init__.py
│           ├── health.py   (11 LOC)
│           ├── sessions.py (223 LOC — POST/GET sessions, lifecycle)
│           ├── config.py   (197 LOC — settings sync + versioning)
│           └── messages.py (0 LOC — budget-cut)
└── frontend/
    ├── index.html          (skeleton-supplied)
    ├── package.json        (skeleton-supplied)
    ├── tsconfig.json       (skeleton-supplied)
    ├── vite.config.ts
    └── src/
        ├── main.tsx        (9 LOC)
        ├── App.tsx         (63 LOC — top-level layout)
        ├── api.ts          (123 LOC — typed fetch client)
        └── FocusSessionTimer.tsx (358 LOC — timer logic + UI)
```

`messages.py` shipping at 0 bytes is the budget-cap fingerprint: M3 contracted it (one of the contract notes references a notification envelope), M5 ran out of budget before implementing it. Everything else is real. Tests exist for messages (`tests/test_messages.py`) so M4 ran on its scenarios — the gap is M5 alone.

The frontend in particular is a strong signal: `FocusSessionTimer.tsx` at 358 LOC is doing real work (countdown logic, state transitions, browser tab visibility handling per the "keep timer running when app closed" feature). The team produced something a small focused team would produce — the README's 5th corollary (analysis 036) cashes out again, and this time on the frontend stack too.

## Findings

### F1 — Skeleton system works end-to-end on first run

T70 (bundle loader), T71 (NewRunScreen picker on bare-root detect), T73 (manifest with `language` + `post_apply` commands) shipped together in 0.2.1 and r40 was the first run to exercise the full picker → apply → launch flow. No bugs hit. The picker fired correctly, the operator selected `fullstack-fastapi-react`, the skeleton applied cleanly (tracked files appeared in `git status`), the workflow ran on top of the laid-down structure.

The deliverable validates the analysis-037 reframe: the trajectory of decline from r35 (mixed Python + TS scattered at root) → r36 (MVC-ish improvisation) → r37 (scattered timer.py + src/*.ts) → r38 (full collapse, 0 LOC production) wasn't a substrate regression. It was structural-default-of-no-skeleton progressively winning out. Restore the skeleton and the team writes into it.

The skeleton wasn't *prescriptive* — the team didn't slavishly follow `src/backend/api/` as the only layout; they invented `models.py` at the backend root and made independent calls about file granularity inside `api/`. The skeleton supplied *intent shape*, not a paint-by-numbers template.

### F2 — Per-meeting budget gate is the new bottleneck (analysis 035 F2 reproducing)

Headline regression at the substrate level: total cost is exactly `$10.000477` against a `$10.00` cap. The team didn't gracefully terminate at $10.00; instead, the M5/M6 meetings continued past the global cap because each meeting's individual budget hadn't fired yet. When the runner-level cap finally caught up, the main thread STUCK and escalated.

This is the same finding as **analysis 035 F2**: the per-meeting budget cap (set in workflow defaults) and the global runner budget aren't reconciled. Workflow YAML declares `budget_dollars: 5.00` per the dev variant intent, but `run_workflow` doesn't enforce it as a hard sum — meetings each get a slice, and overshooting one meeting can take the whole run past the global cap because no meeting has hit its individual gate.

The fix is the deferred roadmap items (`6fdc15fd` — "Decouple structural cap from meeting_budget"; `6a11b29e` — "Phased orchestrator respect runner.budget_dollars"). After the skeleton work landed, this is now the load-bearing follow-up. r40 is a clean reproduction of the failure mode for whoever picks those tickets up.

### F3 — Auto-sentinel notification didn't fire (or didn't reach the operator)

Operator-reported, not yet root-caused: r40 was an unattended run. The escalation note shows the team STUCK on the main thread and Dodo escalated; the auto-sentinel (T69 follow-up) was meant to provide a sentinel response after a configured idle window so unattended runs don't park forever waiting on a human. The run did terminate (`outcome: complete`), so *some* sentinel mechanism resolved the escalation — but the operator received no notification (no toast, no system-level alert) signalling that human input was being requested.

Two possible failure modes, both worth investigating:

1. **The auto-sentinel fired silently and resolved the escalation without notifying** — sentinel response went to the bus, the team consumed it, the deadlock unstuck without ever surfacing in operator-visible UI. If so, the LiveRunScreen modal-with-timer (`auto_dismiss_after`) might have shown briefly while the operator wasn't watching, then dismissed itself.
2. **No sentinel fired; the run terminated via budget-exceeded path independently** — the escalation note exists but the workflow's overall completion came from hitting the $10.00 cap, not from any user-question affordance resolving.

Either way, the operator's mental model — "I'll get a notification if the team needs me" — didn't hold. This is its own ticket worth filing alongside the per-meeting-budget reconciliation work; for unattended runs to be reliable, the operator needs *some* signal (system notification, sound, badge) when a question is pending past the auto-sentinel timer, OR a confidence that the sentinel itself surfaced in the run's final report.

### F4 — Best per-feature efficiency to date (cost AND wall-clock AND LOC-per-dollar)

| Run | $/feat distinct | min/feat distinct | LOC/$ |
|---|---|---|---|
| r35 phased | $1.58 | 15.3 | 0 (no src/) |
| r36 teams | $1.77 | 10.7 | 248 |
| r38 diff v2 | $1.55 | 9.9 | 0 |
| r39 + Guard A | $1.71 | 12.2 | 117 |
| **r40 + skeleton** | **$1.25** | **5.9** | **124** |

r40 produced **half the per-feature wall-clock** of any prior run. Not because the team got faster individually — the per-call cost is similar — but because the team did less *invention* and more *implementation*. The skeleton + the increased feature count pulled the run toward higher-throughput territory.

LOC-per-dollar is similar to r39 (124 vs 117), which is interesting: the skeleton didn't make code production cheaper *per LOC*, it made it more *focused* per feature. The team writes about the same amount of code per dollar; they just write it to the right places without burning calls inventing where those places should be.

### F5 — M2 / M2.5 produced semantic duplicates in the feature manifest

Operator counted "9 features" going in; r40's `features/` directory contains 10 entries with two near-duplicate pairs:

- `feature-002` and `feature-006` both about *configure session durations + sync settings*
- `feature-004` and `feature-007` both about *keep timer running when app closed (+ notification)*

That's 10% feature-manifest waste — the team scoped, decomposed, and ran duplicate work through M3/M4/M5. Caterpillar should have caught this in M2.5 (composition / "what does this claim, does it hold?"); the deduplication step either didn't run that aggressively or was insufficient.

Not blocking, but worth a follow-up: tighten M2.5's directive to explicitly check for semantic overlap across the feature list, not just structural well-formedness. Could also be a Caterpillar §VIII finding about *when does the composition pass collapse parallel features?*

### F6 — Caterpillar nearly absent (7 calls, 0.6% of cost)

r39 had Caterpillar at 33 calls / $0.64; r40 dropped to 7 calls / $0.06. That's not a 9-feature scaling; it's a near-elimination of M6 review. The budget-exceeded outcome correlates: by the time M6 convened (or attempted to), the cap had fired.

The trade is real — the structural cap on Hatter from analysis 035 F1 (M4 phases bound Hatter sprawl) freed budget for Tweedles, who consumed it on M5 implementation, leaving M6 starved. A future run with the budget-reconciliation fix in place should restore Caterpillar to ~30+ calls.

### F7 — Tool-call profile shifts toward navigation when there's structure to navigate

r38 (0 LOC production, no skeleton): tool calls dominated by `write_file` and `str_replace` chasing test fixtures.
r40 (1,243 LOC production, skeleton in place): **80% of tool calls are read_file + list_files**, only 9% are file-modification operations.

This is the right ratio for a TDD loop on a real codebase. The team is reading much more than it's writing — exactly what experienced engineers do. The skeleton creates the *thing-being-navigated*; without it, there's no navigation phase, only invention.

Cat-style architectural caching could probably knock 20-30% of read_file calls off — when the same file gets read 10 times across a run, only the first read carries information. But this is downstream optimization; the navigation-heavy ratio is itself a healthy signal.

## What's next

1. **Per-meeting / global budget reconciliation** (`6fdc15fd` + `6a11b29e`, both P2 → bump to P1?) is now the load-bearing bottleneck. r40 demonstrates the failure mode cleanly. Pick one of the two tickets, ship the fix, re-run pomodoro and watch for graceful budget termination at $5–6 instead of cap-pinned escalation.
2. **Notification ticket for auto-sentinel + unattended runs** (file new) — F3's user-reported gap. Operator should get a system notification when the auto-sentinel timer is about to fire AND when it does. Could be a Textual notification + native OS notification via `notify-send` / equivalent.
3. **M4 per-item parallelization** (`fd5748e5`, P1) — at 10 features × ~5 min/feature = 47 min, parallelizing M4 across iterations should drop wall-clock to ~25 min. Already filed; r40 is the loudest case yet for picking it up.
4. **M2.5 deduplication directive tightening** (file new from F5) — small directive change, probably high ROI given the duplicate-feature waste.
5. **Re-run on `tdd-serial-phased-dev`** (the Haiku 3.5 variant from 0.2.1) — needs a separate analysis. Compare cost/quality on the same skeleton-equipped substrate.

r40 is the strongest deliverable substrate has produced. The next ceiling is structural-substrate (budget reconciliation), not directive-substrate or model capability.
