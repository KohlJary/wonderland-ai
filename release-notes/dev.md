# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

### TUI: Queue action available on in_progress tickets

Validation5 surfaced a stuck-ticket pattern — synthesized follow-up tickets that didn't close cleanly on their implementation pass got marooned in `in_progress`. The dashboard's only action was "Mark done," which would lie about their state. The state machine already permitted `in_progress → queued` (the un-abort path in `ticket_lifecycle.LEGAL_TRANSITIONS`); the UI just wasn't exposing it. Operator can now re-queue a stuck ticket for the next implementation pass without having to fake its completion first.
