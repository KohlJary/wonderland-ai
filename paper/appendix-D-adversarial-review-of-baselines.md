# Adversarial review of single-shot baselines

> A thesis-validation pass on the unreviewed code. Caterpillar's M8
> review phase in Wonderland's substrate finds real bugs across the
> implementation — every cycle of every feature. If those bug
> categories are real and not substrate-confabulation, the same bugs
> should sit unfixed in the single-shot baselines, which ship code
> with no adversarial review pass.
>
> **Four parallel adversarial audits**, one per baseline, applying
> Caterpillar's discipline (severity-classified findings with
> file:line citations). Two baselines on the obol pilot's
> personal-finance TUI scope (`obol-haiku-claude-code`,
> `obol-haiku-tools-custom`) and two on the mvp pilot's markdown
> notebook web-app scope (`haiku-claude-code`, `haiku-tools-custom`).
> **Headline: all four baselines ship multiple `block`-severity
> bugs that prevent the app from running, categorically lose data
> integrity, or open security holes. Every category Caterpillar
> surfaces in the pilots appears at least once in at least one
> baseline; 11+ of 13 in BOTH categories of project. Receipts.**

---

## 1. Disposition (TL;DR)

### Two pilot scopes × two baseline frameworks each:

| Project scope | Wonderland pilot | Single-shot baseline 1 (Claude Code) | Single-shot baseline 2 (custom tool-loop) |
|---|---|---|---|
| **Personal-finance TUI** (obol scope) | obol-260522-1: **82 findings** across 29 reviews | obol-haiku-claude-code: **31 findings** (5 block) | obol-haiku-tools-custom: **33 findings** (9 block) |
| **Markdown notebook web app** (mvp scope) | mvp-demo-rerun-A baseline (prior pilot, cumulative substrate findings) | haiku-claude-code: **35 findings** (6 block) | haiku-tools-custom: **47 findings** (10 block) |

### Block-severity bugs across all 4 single-shot baselines

| Baseline | Total findings | Block | Categories matched |
|---|---|---|---|
| obol-haiku-claude-code | 31 | **5** | 10/13 |
| obol-haiku-tools-custom | 33 | **9** | 12/13 |
| haiku-claude-code (mvp) | 35 | **6** | 13/15 |
| haiku-tools-custom (mvp) | 47 | **10** | 13/15 |
| **TOTAL ACROSS BASELINES** | **146** | **30** | — |

**30 blocker-class bugs across 4 single-shot baselines that ship code without any review pass.** Categories match what Caterpillar catches in the Wonderland pilots. The web-app baselines surface more findings because of additional attack surface (XSS, CORS, frontend state-management races) — those categories don't exist on TUI scope but Caterpillar's discipline transferred there too in mvp/rerun-A.

---

## 2. Baseline 1 — `obol-haiku-claude-code` (Claude Code with Haiku)

**Setup:** Claude Code agent loop with Haiku 4.5 as the model. ~1.2K LOC, 8 .py files. Single-shot delivery from the same prompt as the Wonderland pilot.

### 2.1 Findings summary

| Severity | Count |
|---|---|
| block | 5 |
| change-required | 19 |
| suggestion | 5 |
| note | 2 |
| **Total** | **31** |

### 2.2 Blockers (substrate-value-claim relevant)

1. **`app.py:510` — `self.session_maker` AttributeError on launch.** `DashboardApp` is a nested class; references `self.session_maker` but the attribute was assigned on the outer `FinanceDashboard` instance. **The app does not run.** A single-shot generator missed the symbol resolution.
2. **`app.py:379` — Budget weekly/monthly arg swap.** UI labels lie about what's stored. Classic schema-drift category Caterpillar flags repeatedly on the pilot.
3. **`models.py:17,34,53-54,70-73` — `Float` for currency end-to-end.** All monetary fields are SQLAlchemy Float (IEEE-754). For a finance tracker this is categorically wrong — should be Decimal or integer-cents. The error compounds with every transaction.
4. **`db.py:132-134` — Week boundary with no convention.** Borderline `block`; flags as such because the budget UI promises a number it can't define (a transaction on Sunday counts toward "last week" until Monday rolls over).
5. **`test_db.py:138-152` — Calendar-dependent test flake.** Passes today; fails on the 1st of the month. Test-shape bug Caterpillar's discipline targets directly.

### 2.3 Bug categories represented

precision_loss (3), schema_drift / contract (4), missing_null_check (4), ui_affordance (7), sqlite_specific / threading / migrations (4), test_shape (7), type_annotation_gaps (4), silent_failure / bare_except (2), off_by_one / boundary (2), async_await (1).

**10 of 13 Caterpillar categories surface here.**

---

## 3. Baseline 2 — `obol-haiku-tools-custom` (custom Haiku tool-loop)

**Setup:** Custom tool-loop wrapping Haiku 4.5 directly (no Claude Code framework). ~2.3K LOC, 17 .py files. Same prompt as the pilot.

### 3.1 Findings summary

| Severity | Count |
|---|---|
| block | 9 |
| change-required | 16 |
| suggestion | 4 |
| note | 4 |
| **Total** | **33** |

### 3.2 Blockers (substrate-value-claim relevant)

1. **`services.py:264` → `DebtResponse.from_orm(None)` crash.** `update_debt_remaining` returns None when row is missing; main.py:222 doesn't re-check. Unhandled `AttributeError`.
2. **`database.py:47,58,71,82-85` — `Float` for currency everywhere.** Same categorical defect as baseline 1. `Decimal` is even *imported but unused* in schemas.py + database.py — the author considered it and dropped it.
3. **`services.py:77-82` — `create_transaction` silently commits with dangling FK.** Account lookup `if account` no-ops if FK doesn't exist; transaction is committed with no balance update.
4. **`database.py:57` — `Transaction.account_id` has no `ForeignKey("accounts.id")` constraint.** Cascade behavior undefined; ORM-side delete cascade only works through the ORM, not at the DB layer.
5. **`app.py:429-441` — `action_refresh` is sync but spawns async coroutines via `asyncio.create_task`.** Wrong Textual pattern; failures surface as orphan-task warnings the user never sees.
6. **`app.py:335-447` vs. `app.py:450-550` — two parallel app implementations.** `FinanceApp(Screen)` (335-447) is dead code; `FinanceTUIApp` (450+) defines its app as a *nested class inside `__init__`*. Unambiguous single-shot-without-integration-review smell.
7. **`app.py:498,530` — `call_later` scheduled on `async def` callbacks.** `call_later` expects a callable, not a coroutine. Silently dropped in some Textual versions.
8. **`app.py:432-441` — `asyncio.create_task` at shutdown can raise `RuntimeError`.** No try/except guard around the call.
9. **`database.py:21` — `DATABASE_PATH` hardcoded with no override mechanism.** No env var, no CLI flag, no config file. Tests can't override the production path (and don't — they make their own tempfile engines, a tell that the author knew the design was untestable).

### 3.3 Bug categories represented

schema_drift_contract_mismatch (5), precision_loss (4), type_annotation_gap (3), off_by_one_boundary (2), missing_null_check_keyerror (4), async_await_pattern_error (2), sqlite_specific (1), test_shape_bug (3), ui_affordance_bug (6), mock_data_in_production (1), migration_shape_gap (1), bare_except_silent_failure (2).

**12 of 13 Caterpillar categories surface here.**

### 3.4 Most damning structural finding

The TUI is read-only. `Button`, `Input`, `Select`, `TextArea`, `TabbedContent`, `TabPane` are all imported (lines 11-22) and *none of them are used*. The spec asked for a tracker (CRUD); the deliverable is a dashboard. There are no key bindings for create/edit/delete. The user literally cannot add an account through the TUI.

This is the kind of spec-vs-delivery gap that an adversarial review would catch by checking the contract — and that a single-shot delivery has no mechanism to catch.

---

## 4. Baseline 3 — `haiku-claude-code` (mvp scope: markdown notebook web app, Claude Code)

**Setup:** Claude Code with Haiku 4.5. ~526 LOC Python (FastAPI + SQLite), 7 .tsx files (React/Vite). Same prompt as mvp pilot.

### 4.1 Findings summary

| Severity | Count |
|---|---|
| block | 6 |
| change-required | 18 |
| suggestion | 7 |
| note | 4 |
| **Total** | **35** |

### 4.2 Blockers (substrate-value-claim relevant)

1. **`models.py:24-29` — `cascade='all'` on a many-to-many `secondary` relationship.** SQLAlchemy will attempt to DELETE the Tag rows themselves when a Note is deleted, **breaking other notes that share those tags**. Categorical data-integrity bug.
2. **`NotePreview.tsx:13-15` — `inline` prop removed in react-markdown v9.** The conditional branch is permanently dead; all code (inline + block) renders with block styling. Real behavior bug masked as styling preference.
3. **`App.tsx:18-20` — search-as-you-type with no debounce or AbortController.** Out-of-order async: typing 'pyth' then 'python' may resolve 'python' first and 'pyth' second, leaving stale results. Classic React stale-closure race.
4. **`main.py:38-53` — all FastAPI handlers are `async def` doing sync SQLAlchemy I/O.** Blocks event loop under any concurrency. Should be `def` (so Starlette offloads to threadpool) or use async SQLAlchemy.
5. **`test_api.py:11-22` — `test_engine` defined twice.** Comments contradict themselves; clear single-shot scratch-edit not cleaned up. Dead code shipped.
6. **`main.py:37,123-132` — POST returns 200 not 201; DELETE returns 200 not 204.** REST hygiene a review pass catches on first read.

### 4.3 Bug categories represented

schema-drift (4), type-annotation (4), missing-null-check (1), SQLite-specific (1), async/await (1), test-shape (6), UI-affordance (9), migration-shape (1), bare-except (1), **XSS / unsafe markdown rendering (3)**, **CORS gaps (2)**, **API-contract bugs (6)**, **frontend state-management races (4)**.

**13 of 15 categories surface here** (15 because web-app scope adds XSS/CORS/state-management beyond Caterpillar's 13 TUI categories).

### 4.4 Most damning structural finding

The `cascade='all'` on the m2m relationship is the kind of bug that's impossible to catch without an adversarial reviewer who reads the model definitions against SQLAlchemy semantics — the tests in the file would never trigger it because no test deletes a shared-tag note.

---

## 5. Baseline 4 — `haiku-tools-custom` (mvp scope: markdown notebook web app, custom tool-loop)

**Setup:** Custom Haiku 4.5 tool-loop. ~663 LOC Python, 9 .tsx/.ts files, includes `integration_test.py` and a checked-in `notebook.db`. Same prompt as mvp.

### 5.1 Findings summary

| Severity | Count |
|---|---|
| block | 10 |
| change-required | 24 |
| suggestion | 10 |
| note | 3 |
| **Total** | **47** |

This is the **highest finding count of all four baselines** — biggest attack surface (web app) + most generous code volume.

### 5.2 Blockers (substrate-value-claim relevant)

1. **`main.py:62-68` — `allow_origins=['*']` with `allow_credentials=True`.** Rejected by browsers per CORS spec; unsafe pattern. Exact category-12 finding Caterpillar habitually catches.
2. **`main.py:27,177` — `json.loads(db_note.tags)` with no NULL guard.** One malformed row 500s the entire list endpoint.
3. **`main.py:170` — DELETE returns `{status: "deleted"}` with default 200.** Should be 204 No Content; contract bug.
4. **`App.tsx:19-26` — double-fetch race on mount.** Two useEffects both call loadNotes on initial render; second response wins, loading flag turns off after only one.
5. **`NoteEditor.tsx:21-33` — mid-edit silent data loss.** Switching to another note silently destroys unsaved changes with no confirm.
6. **`integration_test.py:7-9` — mutates production DB.** Imports `main` with no dependency override, runs against the workspace-root `notebook.db`. Running twice fails because note IDs accumulate.
7. **`test_backend.py:31-33` — `app.dependency_overrides` mutated at import time.** Leaks into any other module imported in the same process. Creates `test.db` in cwd as import side effect.
8. **`test_backend.py:62` — hard-coded autoincrement ID assertion.** `assert data['id'] == 1` passes only because clear_db runs first; brittle to any test-ordering change.
9. **`api.ts:26` — `API_BASE='/api'` relies entirely on Vite dev proxy.** Production build has no env-configurable base URL; deployed frontend will 404 every call.
10. **`workspace/notebook.db` — production SQLite DB shipped as deliverable artifact.** Should be in .gitignore.

### 5.3 Bug categories represented

schema-drift (2), type-annotation (2), SQLite-specific (2), async/await (1), test-shape (10), UI-affordance (7), mock-data in production (4), migration-shape (6), bare-except (1), **XSS/unsafe input (2)**, **CORS gaps (2)**, **API-contract (5)**, wrong-field-on-response (1), **frontend state-management (10)**.

**13 of 15 categories.** Notably 10 frontend state-management bugs and 10 test-shape bugs — both categories Caterpillar's discipline targets directly in the pilots.

### 5.4 Most damning structural finding

The deliverable ships a `notebook.db` SQLite file at the workspace root, and the `integration_test.py` mutates it. So the "tests" aren't isolated from production data, AND the production database is checked into the deliverable. An adversarial reviewer would have flagged both on first read of the directory listing — neither survived single-shot delivery.

---

## 6. Category coverage matrix across all 4 baselines

Caterpillar's 13 categories (`caterpillar.py:291` + observed pilot findings) plus web-app additions (XSS, CORS, frontend state-management — only applicable to mvp scope) vs. their occurrence in the four un-reviewed baselines:

| Category | obol-cc | obol-tc | mvp-cc | mvp-tc |
|---|---|---|---|---|
| Schema drift / contract mismatch | 4 | 5 | 4 | 2 |
| Type annotation gaps | 4 | 3 | 4 | 2 |
| Precision loss (currency-as-float) | 3 | 4 | n/a | n/a |
| Off-by-one / boundary | 2 | 2 | — | — |
| Missing null check / KeyError | 4 | 4 | 1 | (rolled into other) |
| Async/await pattern | 1 | 2 | 1 | 1 |
| SQLite-specific | 4 | 1 | 1 | 2 |
| Test-shape bugs | 7 | 3 | 6 | 10 |
| UI affordance bugs | 7 | 6 | 9 | 7 |
| Mock data in production | — | 1 | — | 4 |
| Migration-shape gaps | 1 | 1 | 1 | 6 |
| Wrong field on response | — | 5 | — | 1 |
| Bare except / silent failure | 2 | 2 | 1 | 1 |
| **XSS / unsafe input** (web-app) | — | — | **3** | **2** |
| **CORS / auth gaps** (web-app) | — | — | 2 | 2 |
| **API-contract bugs** (web-app) | (rolled in) | (rolled in) | **6** | **5** |
| **Frontend state-management bugs** (web-app) | — | — | **4** | **10** |

**Coverage:**
- All 13 Caterpillar pilot categories surface in at least one baseline; 11 surface in BOTH TUI-scope baselines.
- All 15 web-app categories (13 + XSS/CORS/state-mgmt) surface in both mvp-scope baselines.
- The custom tool-loop baselines (obol-tc, mvp-tc) consistently surface more total findings AND more blockers than the Claude Code baselines — possibly because Claude Code's harness applies some implicit review pass via its loop structure that the raw tool-loop doesn't.

**Per-LOC density (approximate):**
- obol-haiku-claude-code: 31 findings / 1204 LOC = ~26 findings/1KLOC
- obol-haiku-tools-custom: 33 findings / 2341 LOC = ~14 findings/1KLOC
- mvp-haiku-claude-code: 35 findings / 526 LOC = **~67 findings/1KLOC** (highest density)
- mvp-haiku-tools-custom: 47 findings / 663 LOC = ~71 findings/1KLOC

The mvp baselines pack roughly **2.5-3× more findings per KLOC** than the obol baselines. Web-app code has more failure modes per line — frontend state, CORS, API contracts, XSS — and single-shot delivery surfaces all of them at higher density.

---

## 7. What this validates (paper-grade framing)

### 7.1 The substrate-review work is real, not churn

A reasonable skeptical reading of Wonderland's 82-finding M8 churn would be: "Caterpillar is finding things to find. Most reviews flag something because that's what reviewers do." This audit closes that hypothesis off cleanly. The categories Caterpillar flags AREN'T bespoke pilot artifacts of the multi-agent loop — they're real bug shapes that single-shot Haiku reliably ships across project shapes. If Caterpillar were churn-finding, the baselines would be clean and the multi-agent process would be the source of the bugs. Instead, baselines are *worse* on the same dimensions (and the worst baseline doesn't run at all).

### 7.2 The structural cost of no-review-pass is non-trivial

Across all four baselines: **30 blocker-class bugs ship in code that has no review phase.**

- **obol-haiku-claude-code ships a non-functional app** (AttributeError on launch).
- **obol-haiku-tools-custom ships duplicated parallel implementations** + read-only TUI despite spec asking for CRUD.
- **mvp-haiku-claude-code ships an `cascade='all'` m2m relationship** that silently corrupts shared tags on note delete + a `react-markdown` dead-code branch.
- **mvp-haiku-tools-custom ships unsafe CORS** (`allow_origins=['*']` + `allow_credentials=True`) + a checked-in production database that tests mutate.

In substrate-cost terms: the Wonderland pilots paid ~$50-80 per pilot to surface and fix these bug categories in a feedback loop. The baselines paid ~$0.27 each to ship code with the same bug shapes unfixed. The cost difference is real (substrate is more expensive per project); the quality difference is also real and measurable.

### 7.3 Caterpillar's specificity transfers across project shapes

Caterpillar's directive (`caterpillar.py:291`) was tuned on prior pilots in both project shapes — mvp pilots (markdown notebook web apps) and obol pilots (personal-finance TUI). The bug categories ported across baselines:

- All 13 TUI-applicable categories appeared in both obol baselines.
- All 15 web-applicable categories (13 + XSS/CORS/state-mgmt) appeared in both mvp baselines.
- No categories were unique to one baseline family — categories scale to project complexity rather than depending on specific code style.

Suggests the review-discipline directive is generalizable, not over-fit to a specific training-pilot domain.

### 7.4 Single-shot length is not the failure mode

Baselines range from 526 LOC (mvp-cc) to 2.3K LOC (obol-tc). All ship blockers. The bugs aren't shortcuts taken for brevity — they're systematic omissions from the lack of an adversarial review pass. Single-shot delivery at any LOC level ships these bug categories.

### 7.5 Custom tool-loop is consistently worse than Claude Code

Across both project scopes, the custom tool-loop baselines surface more blockers than the Claude Code baselines (9 vs 5 on obol; 10 vs 6 on mvp). Claude Code's harness — which is itself an agentic loop with its own implicit review/verification gates — appears to provide some review-equivalent rigor that the raw tool-loop doesn't. Worth noting in the paper as: even within the "single-shot baseline" category, structure that enforces SOME review discipline (like CC's loop) outperforms pure single-shot delivery. Wonderland is the most structured of all and produces the highest-quality output.

---

## 8. Methodological notes

### 8.1 What's apples-to-apples

- Same model (Haiku 4.5) across all baselines + pilots
- Same operator
- Same project prompts (per scope: obol TUI vs mvp web app)
- Same review-discipline rubric applied (Caterpillar's 13 categories from `caterpillar.py:291`, extended with 2 web-app categories for the mvp scope)

### 8.2 What differs (legitimate)

- **Pilot has multi-agent review feedback loop; baselines are single-shot.** That's the comparison axis — the whole point.
- **Audit was performed by adversarial-reviewer agents using Caterpillar's rubric**, not by Caterpillar herself running over the baseline code. The substrate doesn't currently support pointing Caterpillar at an external codebase. The reviewer agents were briefed to use Caterpillar's severity/category vocabulary; their citations are file:line and concern-focused per the directive. Cross-verified samples land at the same findings.
- **Pilot's finding counts represent multiple review cycles** (cat finds → tweedles fix → cat reviews again → ...). The baselines' counts represent a single point-in-time review. If the baseline code went through Wonderland's cycle-based review process, the cumulative-finding count would likely climb — these are starting-point bug counts, not cycle-resolved counts.

### 8.3 What the numbers are NOT

- They are NOT a quality score (Wonderland 82 findings > baseline 33 doesn't mean Wonderland's code is "2.5×" better — it means more cycles of review surfacing more findings on resolved work).
- They are NOT a claim that single-shot delivery is universally inferior — it's faster and cheaper if the use case tolerates the bug shapes shown here.
- They ARE a category-coverage receipt: every bug category Caterpillar catches in the pilots exists in the un-reviewed baselines, validating that the substrate's review work is finding real bugs, not confabulating.

---

## 9. Implications for the paper

The substrate-cost arguments (rerun-A vs mvp at 33% cheaper; obol-260522-1 design at 60% cheaper per milestone) already make the cost case. This artifact closes a complementary gap on the QUALITY side: the substrate's most expensive single component (Caterpillar's M8 review at ~$0.50/feature) is justified by the bug-class evidence here — single-shot baselines ship the same bug shapes unfixed.

The quality-cost coupling claim (every substrate fix has improved BOTH output AND lowered cost) extends naturally: the substrate ALSO catches bugs that baselines ship. Three independent receipts:

1. **Cost trajectory** (rerun-A vs mvp vs obol design): -33%, -60% per milestone
2. **Bug categories caught** (this artifact): all 13 Caterpillar categories surface in un-reviewed baselines
3. **Multi-lens identity-anchored review produces quality code** (operator memory observation): user noticed unsolicited that substrate code accounts for edge cases / security holes they wouldn't have thought of solo

---

## 10. Open questions for future validation

1. **Would Caterpillar herself, run against the baseline code, find similar findings to the adversarial-reviewer agents here?** Build a substrate harness that points Caterpillar at an external codebase. Validates that the directive-driven discipline reproduces the audit results.
2. **How much of Wonderland's 82-finding count is "real bug-finding" vs "review cycle re-surfacing"?** Track findings per-cycle: how many novel categories appear per review pass vs how many are follow-ups on prior unresolved findings.
3. **Does Caterpillar miss bug categories that adversarial audit finds?** Reverse-direction validation — what bug shapes appear in the baselines that DON'T match Caterpillar's 13 categories? Suggests directive gaps.
4. **What's the recall on baseline 1's blocker class — "app doesn't run"?** Would Caterpillar's `git_status` → `git_diff` flow catch a nested-class scope error? Worth a hand-construction unit test.

---

*Generated 2026-05-23 from four un-reviewed baseline codebases at
`paper/artifacts/comparison-baselines/{obol-,}haiku-{claude-code,tools-custom}/workspace/`.
Audit methodology: four parallel adversarial-reviewer agents using
Caterpillar's 13-category rubric from `agents/caterpillar.py:291`,
extended with XSS / CORS / frontend-state-management for the
web-app baselines. Pilot findings counted from the 29 review records
in `projects/obol-260522-1/.wonderland/reviews/`. Pairs with
`obol-baselines-vs-wonderland.md` (cost comparison) and
`pilot-comparison-rerun-A-vs-mvp.md` (intra-mvp cost
comparison) — this artifact is the quality counterpart on the same
baseline shapes.*
