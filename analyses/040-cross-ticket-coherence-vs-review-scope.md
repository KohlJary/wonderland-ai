# Analysis 040 — Cross-ticket coherence vs. review scope: a contract drift M8 didn't catch

**Date:** 2026-05-10
**Run:** obol tdd-implement on feature-003 (budget-vs-spend tracker), [obol/.wonderland/telemetry/run-20260510T063934.json](file:///home/jaryk/obol/.wonderland/telemetry/run-20260510T063934.json), $6.63 / $10.00 cap, 28.4 min wall-clock, 744 calls, `outcome: complete`.
**Substrate state:** post-031 design phase, post-cost-attribution fix (`f36bbf7`), post-pipeline-mode (`156e76e`), post-directive-as-seed (`ed082bd`). Run thread ids show legacy `{meeting_id}-{slug}` shape (no `pipe.` prefix), so this was tdd-implement *before* the pipeline-mode commit's YAML wiring took effect on the running session — stage-style dispatch with the new per-thread cost attribution active.
**Result:** **Team produced ~70% of feature-003. The backend half is excellent — `budget_calculator.py` ships with explicit invariants tied back to scenario IDs (refund sign preservation, zero-budget edge, deleted-category defense), 359-line test file, period boundary math handled in UTC. The frontend half has three misses, all of which fall outside what M8's two reviews opened. The gap is not skill — it's *review scope*. M8 reviewed each file in isolation; the missed defects all live in the spaces *between* files: a contract note says one thing, the backend implements 50% of it, the frontend assumes 100% of it, and `App.tsx` never imports the component the work produced. M8's directive lists "cross-ticket coherence" as the third of three review checks — the most expensive one (multi-file context) and naturally the one that gets cut when the meeting budget tightens.**

## What we tested

The first end-to-end implementation run after the design-side workflow split (tdd-design → tdd-implement). Operator queued one feature (`feature-003-budget-vs-spend-tracker`) for implementation; the substrate's lifecycle filter promoted its 4 child tickets to in-flight (031 calc engine, 032 drift detection, 033 frontend display, 034 drift alerts).

Going in, the named risks were:
1. The directive ("Build a TUI dashboard for personal finance — htop for money") had already been ignored at M4 — Cat shipped a federated-SQL ADR that committed the project to FastAPI/React despite the "TUI" stack signal. The directive-as-seed fix (`ed082bd`) is the substrate-side mitigation but doesn't apply retroactively.
2. Tweedles working in stage-style mode (M6 all tickets → M7 all tickets → M8 per feature) on a feature whose tickets touch four files across two stacks (Python backend + React frontend).
3. M8's per-feature review is the only artifact synthesizing across tickets. Its convenor budget is 0.40, smaller than M5/M6/M7's, so it pays for the smallest context window when the cross-ticket gap requires the largest.

What broke is not (1) directly — that miss was already locked in by the prior tdd-design run's ADR. What broke is (3): M8's review caught two real defects (both in `BudgetDisplay.tsx` polling logic), but missed three larger defects living in cross-file gaps.

## Top-level numbers

| Metric | Value |
|---|---|
| Total cost | $6.63 / $10.00 cap |
| Total calls | 744 |
| Wall-clock | 28.4 min |
| Outcome | complete |
| Tickets in scope | 4 (031, 032, 033, 034) |
| M6 (Tea Party) total | $2.85 across 4 ticket lanes ($0.50–$0.97) |
| M7 (Implementation) total | $3.36 across 4 ticket lanes ($0.76–$1.05) |
| M8 (Review) total | $0.41 — one feature-level review |
| LOC shipped | ~2,131 across `src/backend/`, `frontend/src/`, `tests/` |
| Acceptance criteria covered | ~70% (5 of 13 ACs partial-or-missing) |

## Coverage by ticket

| Ticket | Owner | Status | Where it lands |
|---|---|---|---|
| **031 calc engine** | tweedledum | ✅ solid | `src/backend/budget_calculator.py` (199 LOC) — exemplary. Caterpillar review-002 verdict: accept. Invariants quoted with scenario IDs. Refund signs, zero-budget, deleted categories all defended. |
| **032 drift detection** | tweedledum | ⚠️ partial | `>100%` flagged correctly (`overspend_flag = spent > budgeted`). **`>80%` threshold never makes it out of the backend** — `overspend_flag` is false at 85%, the field doesn't carry the warning band. |
| **033 frontend display** | tweedledee | ⚠️ orphaned | `BudgetDisplay.tsx` (298 LOC) is fully built. **`App.tsx` never imports it** — still the skeleton placeholder rendering a `<MessageList>` with the literal comment *"Placeholder UI — replace with real feature components."* |
| **034 drift alerts** | tweedledee | ❌ broken in two ways | (a) Inherits 032's contract gap — `getDriftSeverity` returns `"ok"` at 85% because it ANDs with `overspend_flag` which is false there. The 80–99% case is dead code. (b) Alert summary blocks at lines 287–301 are static `<div>`s with no click handler. AC2 ("user can tap badge to navigate") not met. |

## The systemic miss — contract drift across the M5 → M7 → M7 chain

Reading the design-phase artifacts produced by the prior tdd-design run, the contract is clearly written. From [`contract-notes/contract-note-005-budget-summary-endpoint-contract.md`](file:///home/jaryk/obol/.wonderland/contract-notes/contract-note-005-budget-summary-endpoint-contract.md):

> Frontend assumption: spending is pre-computed per category; overspend flags (**>80%, >100%**) are backend-computed; last_updated supports staleness UX.

The contract names two thresholds. Tweedledee's `api.ts:89` echoes it back verbatim:

```typescript
* Assumptions:
* - ...
* - Overspend flags are backend-computed (>80%, >100%)
* - last_updated timestamp lets frontend show staleness ("last updated X ago")
```

But Tweedledum's `budget_calculator.py:171` ships only one threshold:

```python
if budgeted is not None:
    if budgeted > 0:
        overspend_percent = int(round((spent / budgeted) * 100))
        overspend_flag = spent > budgeted   # ← only fires at >100%
```

And then Tweedledee's `BudgetDisplay.tsx:233-239` and `api.ts:127-134` AND-gate every drift display on `overspend_flag`:

```typescript
const warningCount = summary.categories.filter(
    (cat) =>
      cat.overspend_flag &&                  // ← false at 85%
      cat.overspend_percent !== null &&
      cat.overspend_percent < 100
  ).length;

// and
export function getDriftSeverity(overspendPercent, overspendFlag) {
  if (!overspendFlag || overspendPercent === null) return "ok";  // ← 85% lands here
  if (overspendPercent >= 100) return "critical";
  return "warning";   // dead code
}
```

The outcome: a category at 85% of budget shows `severity = "ok"`, no warning badge, no alert summary entry. The whole reason ticket-034 exists ("notify user when category hits 80%") is silently dropped.

This isn't a design failure — the design phase produced a contract that explicitly mentioned both thresholds. It's an *implementation drift* between two Tweedles working independently, where the contract was a third document neither of them re-read at integration time. M8's job is to catch exactly this.

## What M8 actually reviewed

Two reviews shipped. Both are technically rigorous within their scope:

**[review-001](file:///home/jaryk/obol/.wonderland/reviews/review-001-budgetdisplay-polling-logic-dependency-array-causes-state-loop.md):** `BudgetDisplay.tsx` polling logic — verdict: request-changes. Two real bugs caught: (1) `useCallback` dependency array includes transient state (`pollInFlight`, `loading`), causing the callback to be recreated on every poll cycle and triggering the parent useEffect to clear/restart the interval — defeating the 30s cadence. (2) The overlap guard reads `pollInFlight` (React state, asynchronous) instead of a synchronously-updated ref. Quote-perfect line numbers, accurate API misuse diagnosis.

**[review-002](file:///home/jaryk/obol/.wonderland/reviews/review-002-budget-calculator-refund-and-edge-case-handling.md):** `budget_calculator.py` refund + edge cases — verdict: accept. Praises the refund sign-preservation invariant, zero-budget handling, period boundary math, deleted-category defense.

Both reviews opened *one file*. Neither review opened the contract notes. Neither opened files from across the backend/frontend boundary. Neither read `App.tsx` to see whether the BudgetDisplay component was actually wired in.

The M8 convenor directive in `tdd-implement.yaml:178-191` does name three checks:

1. Does the code match the contract?
2. Do the tests cover the acceptance criteria?
3. **Cross-ticket coherence.** Tickets ship in serial; the ticket-N implementation might not yet be in the codebase when ticket-N+1 is implemented. M8 sees the cohesive feature deliverable — call out integration gaps.

The directive is correct. Its third clause names exactly what was missed. But "cross-ticket coherence" requires reading 4 files at once (contract note + backend + frontend + integration point) where the other two checks scope to one file at a time. With $0.41 of meeting budget, Caterpillar made the cheap calls and let the expensive one slip.

## Root cause: directive lists checks without ranking them

When a meeting budget tightens, the agent picks the cheapest checks first. Cat's M8 ran 5 phase rotations against a 0.40 cap and shipped two single-file reviews — both correct, but neither answering the integration question.

The directive's structure invites this. "Three checks: A, B, C" reads as "do all of them" but in practice equals "do whatever fits in budget." The third check (multi-file) is naturally the largest-context, so it gets cut.

Two competing frames for the fix:

**Frame A — Reorder checks.** Make the cross-ticket coherence check happen **first**, before per-file reads. Caterpillar opens the contract notes + at minimum one upstream emitter and one downstream consumer file together. Verifies they agree on field semantics. Per-file reviews come second. If budget runs out, the integration check has already shipped.

**Frame B — Split the meeting.** M8 becomes two iterations: M8a integration review (cross-file, one feature) + M8b per-file deep review (one file at a time, multiple iterations). M8a is the gate; M8b is detail polishing. Doubles the review meetings but each has a clear scope.

A is cheaper to ship and better-shaped to the actual failure mode here. B is more defensible substrate-level but compounds budget pressure (already $6.63 / $10.00 in this run; doubling reviews tightens the cap).

Recommendation: ship A first. Promote "cross-ticket coherence" to **the first check** in M8's convenor_directive, with explicit instructions about what files to open. Watch a real run for whether Caterpillar starts catching contract drift. Frame B is the substrate move if A doesn't hold.

## The App.tsx orphan

A separate failure mode worth naming: `frontend/src/App.tsx` contains the literal text *"Placeholder UI — replace with real feature components."* No ticket references App.tsx by name; it's part of the skeleton (the `fullstack-fastapi-react` template). Ticket 033 says "render a visual breakdown" — but rendering happens at the App-level, not just the component-level. Tweedledee built `BudgetDisplay` but never replaced the App.tsx scaffold to use it.

This is the **skeleton-parasitism** failure mode named in [analysis 039](./039-skeleton-parasitism-and-m25-silence.md), in a milder form. r41-obol shipped *no obol-specific code* because the team got captured by a CounterScreen example. r42-obol (this run) shipped a real BudgetDisplay component but didn't wire it in — the skeleton's App.tsx is doing what its comment says (render messages) and the team didn't notice they needed to replace it.

The skeleton gives the team a working baseline; the assumption is that the team will replace skeleton-default UI with feature UI. That assumption isn't enforced anywhere in the substrate. Caterpillar's review of `BudgetDisplay.tsx` would have caught it if she'd opened App.tsx in the same review — back to the cross-file scope problem.

## What this run does NOT show

This run does not show whether the directive-as-seed fix (`ed082bd`) helps Cat's M4 stay grounded — that fix lands on tdd-DESIGN, and this is a tdd-IMPLEMENT run. It also does not show whether pipeline-mode (`156e76e`) helps or hurts integration coherence — the run used legacy stage-style dispatch (thread ids confirm). Both fixes need their own first-runs.

This run also does not isolate whether the skeleton-parasitism risk is reduced. The team built the right component; the App.tsx miss is on the boundary between skeleton and feature, where the substrate currently has no opinion.

## Findings

**F1 — M8's three checks are listed without budget-aware ordering.** Cross-ticket coherence is named third, sized largest, and consistently cut when the meeting budget tightens. Ship by promoting it to first and naming the files Caterpillar should open together.

**F2 — Single-file review default reproduces.** Both M8 reviews this run opened exactly one file. Neither read contract notes alongside code, neither checked App.tsx integration, neither cross-checked backend ↔ frontend semantics. Pattern matches r41's M2.5 failure where Caterpillar's review was rigorous but scoped to the wrong artifact.

**F3 — Contract drift is the canonical cross-ticket bug.** When Tweedles work on adjacent tickets in serial, contract notes encode the integration agreement, but the implementation phase doesn't re-read them. The 80%/100% threshold mismatch is identical to a class of bugs that any cross-team integration produces (see also: api.ts:89 explicitly documenting the assumption that turned out false).

**F4 — Skeleton-parasitism v2: the App.tsx orphan.** Skeleton-provided integration scaffolds (App.tsx routing, top-level state, mount points) need to be explicitly named in tickets or M8 review scope. Otherwise the feature gets built as a component-shaped artifact that never reaches the user.

**F5 — Per-thread cost attribution holds under feature-scoped runs.** Telemetry `per_thread_cost` shows clean per-iteration spend with no cross-iteration leakage. The fix from `f36bbf7` is doing its job. Each lane's M8 review-feature-003 cost ($0.41) cleanly separates from each ticket-level meeting cost.

## Open questions

- Does Frame A (reorder M8's checks) actually change Caterpillar's behavior, or do single-file reviews keep happening because the model-level prior is "review one file at a time"? Constitutional clause may be needed if directive-level reframing isn't enough.
- The pipeline-mode runtime now lives in main but hasn't been exercised on a real run yet. Does pipeline mode change M8 review patterns at all? (It shouldn't — M8 still runs once per feature, just within a lane — but worth confirming.)
- Should App.tsx orphan be a substrate-level concern or a per-skeleton concern? Each skeleton has its own integration point (App.tsx for React, mod.rs for Rust, etc.). Maybe the skeleton itself ships a per-skeleton checklist M8 can read.

## What lands next

This analysis suggests one shippable substrate change: **reorder M8's convenor directive to put cross-ticket coherence first**, with concrete file-list guidance ("open the contract note + at least one backend file + at least one frontend file before any per-file review"). That's a YAML-only change, low risk.

Skeleton-parasitism v2 (F4) wants a separate fix — likely a ticket on each skeleton template to declare its integration-point files (App.tsx, mod.rs, main.go) so M8 can include them in its review scope. Defer.
