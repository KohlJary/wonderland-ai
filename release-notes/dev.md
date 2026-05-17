# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

### TUI: Queue action available on in_progress tickets

Validation5 surfaced a stuck-ticket pattern — synthesized follow-up tickets that didn't close cleanly on their implementation pass got marooned in `in_progress`. The dashboard's only action was "Mark done," which would lie about their state. The state machine already permitted `in_progress → queued` (the un-abort path in `ticket_lifecycle.LEGAL_TRANSITIONS`); the UI just wasn't exposing it. Operator can now re-queue a stuck ticket for the next implementation pass without having to fake its completion first.

### TUI: Live Call feed actually displays calls for subprocess runs

The Live Call feed in `LiveRunScreen` was reading `runner.telemetry.entries` directly via `getattr(self.handle, "_runner", None)`. That only works for in-process runs — the default `wonderland run-bg` path uses `SubprocessRunHandle` which has no `_runner` attribute (the runner lives in a separate process), so the feed stayed blank for every real pilot.

Replaced with an event-driven implementation: the dispatcher's `AgentActed` events now feed the table directly. Works for both in-process and subprocess runs since event streams are the common interface. Per-call rows show `time · agent · phase` (cost-per-call isn't on `AgentActed`; the per-agent rollup still lands in the status bar via `AgentTelemetryDelta`). Past events get buffered (capped at 200) so meeting-selection changes can replay historical activity for the newly-focused thread instead of leaving the operator staring at residue from the prior filter.

### New directive: ``notebook`` — paper-MVP-ready fullstack demo

Reference directive for the Wonderland paper's reproducible MVP. Single-user markdown notebook with SQLite persistence, FastAPI backend, React + Vite frontend, client-side markdown rendering, tags, search. Designed so a paper reader can clone the repo, run the demo, and verify a working app in <5 minutes of post-install time — no signup, no user data input required.

Differentiated from the existing ``markdown-notes`` directive (which is the pure-frontend, no-backend stress-test variant) — ``notebook`` exercises the full discovery → milestone → tdd-design → tdd-implement pipeline and produces a reviewable full-stack artifact.

Target economics: 5 features × ~$5-15 = $30-60 total MVP spend. The reference cost point we'll cite in the paper.

### Fix: review-synthesized tickets weren't getting marked done after their iteration

Validation5 surfaced a ticket-state drift: 4 review-synthesized follow-up tickets shipped through implementation cleanly (Tweedles worked the threads, Caterpillar reviewed the result) but their lifecycle stayed stuck at ``queued`` instead of progressing to ``done``. Inflated the operator-visible queue count and broke cost-per-feature attribution math.

Root cause: ``_route_blocking_review`` and ``auto_complete_iteration_tickets_on_accept`` both have an auto-complete loop that marks worked tickets done — but the loop's guard required ``state == TicketState.IN_PROGRESS``. Tickets that were queued for the iteration but never had their ``queue → in_progress`` transition fire hit the guard and got skipped.

Fix: both auto-complete paths now fast-forward ``queued → in_progress`` before the done mark when they encounter a queued ticket. Same back-fill pattern that already handled ``None → in_progress``; extended to cover the queued case.

### tdd-decompose workflow + dashboard "Decompose tickets" button

New workflow for the partial-design-rerun use case: features that
landed in ``designed`` state but with insufficient or wrong ticket
sets. Validation5 surfaced the immediate need — features 4 + 5 had
zero tickets attributed (M3 slug drift left the parent feature
slugs out of the synthesized ticket sources), making them
undeployable from the implementation queue.

Three pieces ship together:

- **New lifecycle transition**: ``FeatureState.DESIGNED → IN_DESIGN``
  is now legal. The operator's "I want to redo this feature's
  decomposition" move; was previously a dead-end (designed could
  only go to queued or rejected).
- **New workflow** ``tdd-decompose.yaml``: M3 (decomposition) +
  M3.5 (consolidation) only, filtered on ``in_design``. Features
  picked up from disk via seed-fallback; M3.5 transitions back to
  ``designed`` so the operator can queue for implementation. Budget
  defaults to $1.00 (typical decompose pass is $0.10-$0.30 per
  feature).
- **Dashboard button** "Decompose tickets" on ``designed`` features.
  Transitions the feature back to ``in_design``; the operator then
  runs ``tdd-decompose`` from the run-launcher. Mirrors the
  Queue → tdd-implement UX pattern.

Known limitation: re-decomposing a feature that already has tickets
on disk will accumulate duplicates unless M3.5 actively consolidates
them (which it can, but discipline-dependent). Long-term substrate
fix is snapshot semantics for tickets, parallel to milestone_plan
snapshot semantics in 0.7.0; tracked as roadmap follow-up.

### M9 verify adds pytest_passes alongside pytest_collects

Three-tier verification now runs at end of each feature lane:
pytest_collects (do the tests import?) → pytest_passes (do they pass?) → npm_build (frontend TypeScript + Vite build).

Validation5 feature 2 surfaced the empirical motivation: Caterpillar's M8 review verdict was clean accept on code that didn't actually run. Three runtime bugs the static review couldn't see:
1. Schema drift — `Session` model declared `synced_at`; live SQLite DB had stale schema; every endpoint returned 500 with `OperationalError: no such column`.
2. Contract drift — test expects `synced_at` set on online create, impl returns None.
3. Datetime tz mismatch — `server_updated_at >= client_updated_at` raised `TypeError: can't compare offset-naive and offset-aware datetimes` at runtime.

All three would have synthesized follow-up tickets if `pytest_passes` had been in the M9 chain. Now it is. Next implementation pass picks up the bugs as queued tickets via the existing `_route_blocking_review` path.

### Tea-party skips review-synthesized tickets by default

Cost optimization for the review-loop iterations. Review-synthesized tickets (the ones the substrate creates from Caterpillar's M8 findings) come with a complete spec built in — `location` + `quote` + `read` + `concern` + `request` — so the adversarial test-scenario design pass (tea-party / M6) was adding ~$0.50/ticket of overhead for what's structurally a code-correctness restoration on already-tested paths.

Two new fields land:

- `TicketPayload.source` (TicketSource enum: `m3_decomposition` | `review_synthesis` | `operator`). Default `m3_decomposition`. Auto-set to `review_synthesis` when the substrate synthesizes a follow-up ticket from a review finding.
- `TicketPayload.test_coverage_required: bool | None`. Operator/agent override on the tea-party iteration filter. `None` (default) = use source-based default (`m3_decomposition` and `operator` pass through; `review_synthesis` skips). `True` forces tea-party inclusion; `False` forces skip.

Plus `ReviewFinding.test_coverage_required: bool` (default false) so Caterpillar can mark a finding at review time as needing fresh test design — the synthesized ticket inherits the flag. Caterpillar's directive in `tdd-implement.yaml` M8 teaches when to set it (genuinely new behavior the existing tests don't cover, e.g. "add JWT validation," "implement retry with backoff").

Tea-party gets a new `requires_test_design: true` field in `tdd-implement.yaml`; substrate filters per-ticket in `_run_inner_block` via the `read_ticket_needs_test_design` helper. Completion events still fire for skipped tickets so dependency-gated downstream lanes don't hang.

Expected savings: ~$0.50/ticket per review pass × 2-5 follow-up tickets per pass × 2-3 review passes per feature × 5 features = ~$20-35 saved across a 5-feature MVP. 10-15% cost reduction.
