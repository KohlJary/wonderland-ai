# Analysis 041 — The substrate found the bugs but couldn't close the loop

**Date:** 2026-05-10
**Run:** obol2 tdd-design + tdd-implement, 4 telemetry runs totaling **$18.25** across the design + implement arc:
- 3 design passes: $2.95, $1.57, $2.12 (~$6.62 total)
- 1 implement pass: $11.62, [obol2/.wonderland/telemetry/run-20260510T124928.json](file:///home/jaryk/obol2/.wonderland/telemetry/run-20260510T124928.json), 927 calls, two queued features through the new two-level pipeline.

**Substrate state:** 0.3.3 + five post-release patches (`1546581`, `54a1c24`, `d3ff8b6`, `dcec940`, `170fa61`, `428775e`, `40dfadb`). First end-to-end run with the two-level pipeline shape (outer feature sequential, inner ticket parallel) and the `Feature.kind` discriminator both live. Stack: Python TUI (Textual + SQLite), one project rooted in `~/obol2` from the standard `python-tui` skeleton.

**Result:** **The substrate produced the right shape but couldn't close its own loops.** Sensible module separation (canonical `db.py`, `models.py`, `import_csv.py`), real TDD scaffolding (39 unit tests passing), and Caterpillar's M8 reviews caught the cross-ticket coherence bugs with surgical precision — naming files, line numbers, and contract notes. But the loops the substrate opened didn't close: M8's "block" verdicts have no follow-up primitive, M6/M7/M8 hit budget walls 2× over their declared caps and never fired `transition_iteration_to`, and 4 lanes of parallel ticket work produced 4 divergent CSV import modules with no auto-consolidation. Operator labor was load-bearing — manual feature splits, manual lifecycle advances, manual dup cleanup were what turned the run from "stuck at queued" into "ready_for_review." The thesis (small model + strong constitution = real architectural work) holds for *producing* shape; it does not yet hold for *converging* shape. P13's substrate work has to close that gap.

## What we tested

First end-to-end implementation run after the two-level pipeline ship (`54a1c24`) and the `Feature.kind` discriminator (`d3ff8b6`). Operator started fresh in `~/obol2` from the python-tui skeleton, ran tdd-design three times (iterating directive + recovering from M3/M5 skip bugs that became 0.3.3's lifecycle fix bundle), then ran tdd-implement once with two manually-split features queued.

Going in, the named risks were:

1. **Cross-lane file collisions in M7.** The two-level pipeline is feature-sequential / ticket-parallel — within a feature, multiple tickets touch `src/` concurrently. The Tweedles use `str_replace` for surgical edits, but two tickets writing to overlapping module names is the obvious failure mode and analysis 040 already named it.
2. **M8 review-as-blocker without a fix-it loop.** M8 produces verdicts but no primitive consumes a "block" verdict to spawn revision tickets. Worth seeing how visible the gap is in practice.
3. **Budget calibration is unverified.** M6 0.50, M7 0.70, M8 0.40 were guesses based on tdd-serial-phased timing. Real numbers would surface in the first run.

What broke is largely all three at once, but in ways that compound: lane collisions produced 4 divergent CSV import modules + 2 divergent query modules; budget calibration was 2-2.5× off across every meeting which prevented transitions from firing; the missing follow-up loop meant Caterpillar's reviews diagnosed the divergence but couldn't drive its consolidation.

## Top-level numbers

### tdd-design (3 passes total)

| Pass | Cost | Calls | What it produced |
|---|---|---|---|
| 1 (`run-20260510T115525.json`) | $2.95 | 392 | First M1+M2+M4 — produced 4 features at `designed`; M3/M5 silently skipped (lifecycle fix `1546581`/`2aa46b3` not yet integrated) |
| 2 (`run-20260510T120501.json`) | $1.57 | 97 | Second pass after fixes — quiet, mostly cross-run continuity confirmation |
| 3 (`run-20260510T122747.json`) | $2.12 | 69 | Third pass — Caterpillar churning concerns about story-001 visibility (consumed_by-filter confusion that became fix `170fa61`) |

### tdd-implement (one pass, two-level pipeline)

| Metric | Value |
|---|---|
| Total cost | $11.62 / no cap set |
| Total calls | 927 |
| Features queued | 2 (`transaction-storage-and-csv-ingestion`, `current-month-cash-flow-snapshot`) |
| Lanes spawned | 2 outer (sequential) × 2 inner (parallel per feature) × 3 stages (M6 → M7 → M8) = 10 thread spans |
| Pipeline shape outcome | Worked — feature-A finished its M6+M7+M8 before feature-B's M6 started; within a feature, ticket A and B's M6 ran concurrently |

### Per-agent cost breakdown (implement pass)

| Agent | Calls | Cost | Notes |
|---|---|---|---|
| tweedledum | 405 | $4.51 | Backend Tweedle — schema, CSV parser, query functions |
| tweedledee | 378 | $4.08 | Frontend Tweedle — Textual widgets, dashboard view |
| mad_hatter | 109 | $2.07 | Test scenarios (and some leakage into M7 — see below) |
| caterpillar | 35 | $0.95 | M8 reviews (5 of them) |

### Budget vs actual (per meeting)

| Meeting | Declared budget | Actual avg | Over by | Outcome |
|---|---|---|---|---|
| M6 (Tea Party) | $0.50 | $1.14 | 2.3× | MEETING_BUDGET on every iteration |
| M7 (Implementation) | $0.70 | $1.31 | 1.9× | MEETING_BUDGET on every iteration |
| M8 (Review) | $0.40 | $0.90 | 2.25× | MEETING_BUDGET on every iteration |

Every per-ticket meeting and every per-feature M8 hit budget cap. Zero of them reached `outcome == "COMPLETE"`. Therefore zero `transition_iteration_to` fires. Both queued features stayed at `queued` despite all their tickets actually being implemented.

## Section 1 — The two-level pipeline shape worked

The first thing that landed cleanly: **the new `pipeline.levels: [feature(seq), ticket(par)]` shape ran without crashes**, ticket A1's M6 finishing immediately advanced ticket A1 to M7 while A2 was still in M6 (visible in the live-watch transcript and reproducible from the per-thread cost order). Cross-lane seed isolation held — feature-A's M8 review notes don't reference feature-B's tickets, so the `lane_thread_prefix` filter is doing its job. The dispatch logic in `_run_inner_block` (introduced in `54a1c24`) handled the merge-async-iterators path correctly under real LLM latencies.

**This is the operational claim of the multi-level pipeline machinery validated.** The shape is reusable for any future workflow that needs nested item lanes (the framing in the commit message — "epic→feature→ticket" — is now plausible).

## Section 2 — Cross-lane file collisions: 4 CSV import modules, 2 query modules

The cost-of-parallel showed up exactly where analysis 040 predicted. Mid-implement-run, `~/obol2/src/` accumulated:

```
src/csv_import.py          287 LOC  ← frontend Textual widget (single concern, fine)
src/import_csv.py          272 LOC  ← backend CSV logic, uses src.models (canonical)
src/backend/import_csv.py  209 LOC  ← duplicate backend, inline-defined ImportResult/ParseError
src/backend.py             391 LOC  ← shadowed dead code (Python prefers the package)
```

Four files. Three implementations of `import_transactions_from_csv`. Two definitions of `ImportResult` and `ParseError` (canonical in `src/models.py`, inline duplicate in `src/backend/import_csv.py`). The frontend (`src/csv_import.py`) imported the *divergent* `ImportResult` from `src/backend/import_csv.py`, which is a contract drift bug exactly of the kind analysis 040 named.

Same pattern on the query side:

```
src/queries.py              291 LOC  ← unused shadow code (no exception handling)
src/backend/database.py     313 LOC  ← canonical (used by tests via src.backend re-export)
```

Two implementations of `get_monthly_snapshot` and `get_crisis_status`. Differences subtle: one raises `IndexError` on bad month, the other returns `None`. The kind of divergence that bites later when the wrong one gets imported.

What's interesting is that **the substrate itself partially self-corrected once.** `src/backend/database.py` was a 23-line deprecation shim earlier in the run, re-exporting from `src/db.py`:

```python
"""Re-export from src.db for backwards compatibility.
NOTE: This module is DEPRECATED. All database initialization code lives in src.db.
Do not import from this module in new code. Imports here will be removed in v2.
"""
from src.db import (get_db_path, get_connection, close_connection, ensure_schema)
```

A Tweedle in an earlier ticket noticed the dup, wrote the shim, and *then a later ticket re-grew the file to 313 lines of fresh implementations.* The shim got overwritten. So self-correction happened but didn't stick — there's no substrate primitive that prevents a Tweedle in lane B from re-implementing what lane A already consolidated.

## Section 3 — M8 caught everything, but caught is not the same as fixed

Caterpillar produced **6 M8 reviews**, every single one nailing real defects:

| Review | Verdict | What it caught |
|---|---|---|
| 001 (CSV) | block | Amount-validation rejects zero/negative (contract says any numeric); duplicate implementations |
| 002 (CSV) | block | Same amount-validation bug + duplicate implementations |
| 001 (transaction-storage) | request-changes | Test/contract mismatch on description being required vs optional |
| 003 | request-changes | Uncategorized transactions excluded from spending breakdown |
| 004 | request-changes | Two implementations of `get_monthly_snapshot` and `get_crisis_status` |
| 005 | request-changes | Return type `Optional` where None shouldn't occur |

These are not vague concerns. They quote line numbers, name contract notes, propose specific fixes ("delete src/queries.py, promote src/backend/database.py as canonical"). This is exactly what M8 was specced to do per analysis 040.

**But none of them got fixed by the substrate.** Operator did the cleanup (manual `rm` of three duplicates, manual edit of two import lines) before this analysis was written. Without operator intervention, the divergent state persists indefinitely on disk — there is no primitive in the workflow that consumes `Verdict: block` and spawns revision tickets back through M6/M7. M8's job ends at producing the verdict.

This is the missing follow-up loop. The natural shape would be something like:

- M8 ships verdict=block + a list of `revision_tickets`
- A new meeting (M9? "the trial-revision loop"?) iterates per revision_ticket and routes the work back through M7-with-context
- transition: feature stays in_progress until verdict=approve

P13 doesn't have this. It's a real gap.

## Section 4 — Budget aborts swallowed every lifecycle transition

This is the surprise finding of the run. Every meeting hit `MEETING_BUDGET` outcome. Every. Single. One. Which means `outcome == "COMPLETE"` was false for every meeting, which means `_apply_post_meeting_transitions` (the just-fixed phased-path hook from `2aa46b3`) early-returned, which means `transition_iteration_to` never fired.

End state:

```
transaction-storage-and-csv-ingestion: queued
current-month-cash-flow-snapshot: queued
```

Both features still at `queued` *despite all their tickets being implemented and all their M8 reviews on disk.* From the dashboard's perspective the run did nothing. The operator had to manually append `queued → in_progress → ready_for_review` records to feature-states.jsonl to advance the lifecycle past the budget aborts.

Two distinct failures here:

1. **Budgets are calibrated wrong.** M6 0.50 vs actual $1.14 average is 2.3× under. The numbers came from tdd-serial-phased's stage-style runs which had different convergence dynamics; the ticket-parallel pipeline shape needs its own calibration. Quick fix: bump M6/M7 to ~$1.50 and M8 to ~$1.00.

2. **`outcome != COMPLETE` shouldn't strand artifacts that already shipped.** If M6 produced a test scenario, M7 produced an implementation, and M8 produced a review, the *artifacts exist regardless of whether the meeting hit budget cap.* The lifecycle transition gate on `COMPLETE` was a conservative default; it's now provably wrong for budget-aborted meetings that emitted their target artifact. The right rule is closer to: "if the meeting's exit_condition_artifact landed AND the meeting's intended state transition is legal, fire it" — independent of whether the team converged on quiescence or hit budget cap.

This is a more nuanced fix than just bumping budgets. Bumping budgets buys a single run; fixing the transition rule prevents the class of "everything shipped but lifecycle says queued" bugs forever.

## Section 5 — Operator labor was load-bearing

Counting the operator's actual interventions during this arc:

1. **Manual feature split.** The original M3 over-decomposed feature-001 into 13 tickets with 3× duplicates (3 schema-init variants, 3 CSV-import variants). Operator manually split into 3 right-sized features (foundation + capability + capability), dropped 7 duplicates, re-pointed surviving tickets' Sources lines, and back-filled lifecycle states. This was a substantial editing pass — not a single command.
2. **Manual lifecycle advance.** Both queued features stuck at `queued` after implement run; operator appended 4 transition records to feature-states.jsonl.
3. **Manual dup cleanup.** Three files deleted (`src/backend.py`, `src/queries.py`, `src/backend/import_csv.py`) plus two import lines updated in `src/csv_import.py` to point at canonical modules.
4. **Live constitutional fixes.** Mid-arc, operator surfaced the Hatter-sprawls-into-M7 problem, the M2 consumed_by-filter confusion, the dependency-groups packaging bug. All three became commits during the session (`428775e`, `170fa61`, `40dfadb`).

The substrate did the work that scaled with code volume (writing modules, writing tests, writing reviews). The operator did the work that required *judgment about scope* (which duplicates to keep, which transitions to fire, which features should split, which agents to fix).

This is consistent with how a senior reviewing a junior's PRs operates — but the framing of Wonderland-as-substitute-for-junior-engineer doesn't account for the operator labor. The framing of Wonderland-as-force-multiplier-for-senior-engineer does.

## Section 6 — Hatter's scenario sprawl, with receipts

Quick sub-finding worth noting: **97 test scenarios shipped in M6 across the run, against 18 actual `.py` files in the resulting codebase.** Many scenarios duplicate each other across naming variants (`scenario-001-csv-import-parse-validate-insert.md` vs `scenario-001-csv-import-validation-and-persistence.md`). Hatter's §V instinct is "more coverage" and his engagement rules fire him on most ticket-context utterances.

The fix `428775e` (drop Hatter from M7's roster) lands one part of this. The remaining drift surface is M6 itself — Hatter shipping multiple scenarios per ticket, where one would do. This is a tea-party-budget calibration question + maybe a Hatter constitutional clause about "one scenario per acceptance criterion, not one scenario per *aspect* of an acceptance criterion."

Not urgent, but worth tracking.

## What needs to ship before the next implement run

Ranked by what gates the most operator labor:

1. **Auto-dedup at meeting close (T95 in P13).** Stops the bleeding at the source — M2 doesn't ship duplicate features, M3 doesn't ship duplicate tickets, M7 doesn't write duplicate modules. Highest ROI by far.
2. **Lifecycle transition fires on artifact-landed regardless of meeting outcome.** Stops the "everything shipped but lifecycle says queued" failure mode that bit this run completely. Probably one if-statement change in `_apply_post_meeting_transitions`.
3. **Budget calibration based on real numbers.** Bump M6/M7 to ~$1.50, M8 to ~$1.00. Cheap; should ship in 0.3.4.
4. **M8 block verdict spawns a revision loop.** Larger primitive (new meeting? revision_ticket artifact kind?). Worth a dedicated P13 task; not blocking 0.3.4.
5. **Hatter scenario count per ticket, not per aspect.** Constitutional prose change. Not urgent.

## Closing — was the $18 worth it?

For a research run validating the substrate's shape: yes. The two-level pipeline ran. The `Feature.kind` discriminator survived an end-to-end pass. Caterpillar's M8 review caught real cross-ticket bugs with surgical citations. The lifecycle plumbing worked enough that operator could trace progress.

For a substitute for a junior engineer's first sprint on a personal-finance TUI: not yet. The codebase is real (~1300 LOC across 9 cleanly-separated modules, 39 passing tests, working SQLite + CSV pipeline + Textual app). But getting there required ~30 minutes of operator labor to split features, advance lifecycles, clean up dups, and write the live constitutional fixes that became commits. Without the operator, the run produces a foundation buried under 4 divergent CSV importers and 2 features stuck at queued.

The thesis (Haiku + strong constitution = real architectural work) is intact for *producing* shape. It needs P13 to hold for *converging* shape.
