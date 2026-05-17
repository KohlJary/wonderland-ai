# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

### TUI: Queue action available on in_progress tickets

Validation5 surfaced a stuck-ticket pattern — synthesized follow-up tickets that didn't close cleanly on their implementation pass got marooned in `in_progress`. The dashboard's only action was "Mark done," which would lie about their state. The state machine already permitted `in_progress → queued` (the un-abort path in `ticket_lifecycle.LEGAL_TRANSITIONS`); the UI just wasn't exposing it. Operator can now re-queue a stuck ticket for the next implementation pass without having to fake its completion first.

### TUI: Live Call feed actually displays calls for subprocess runs

The Live Call feed in `LiveRunScreen` was reading `runner.telemetry.entries` directly via `getattr(self.handle, "_runner", None)`. That only works for in-process runs — the default `wonderland run-bg` path uses `SubprocessRunHandle` which has no `_runner` attribute (the runner lives in a separate process), so the feed stayed blank for every real pilot.

Replaced with an event-driven implementation: the dispatcher's `AgentActed` events now feed the table directly. Works for both in-process and subprocess runs since event streams are the common interface. Per-call rows show `time · agent · phase` (cost-per-call isn't on `AgentActed`; the per-agent rollup still lands in the status bar via `AgentTelemetryDelta`). Past events get buffered (capped at 200) so meeting-selection changes can replay historical activity for the newly-focused thread instead of leaving the operator staring at residue from the prior filter.
