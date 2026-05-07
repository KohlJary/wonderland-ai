## Scenario: Jamie's session is restored from IndexedDB, but the session record is stale—server has a newer version from another device

**Severity:** silent-wrongness

**Setup:**

Jamie creates a session on Device A. It goes pending. Jamie updates the session to 'completed' on Device A and the update reaches the backend. Hours later, Jamie opens the app on Device B (which has an older copy of Jamie's IndexedDB from an earlier sync). The app restores the session from IndexedDB on Device B, which still shows the session as 'pending'.

**Trigger:**

Jamie opens the app on a device that has an older copy of IndexedDB than the actual server state.

**Expected:**

The session on Device B should synchronize with the server before being displayed, or at least flag to Jamie that the session state may be stale. The session should show 'completed' with the actual duration, not 'pending'.

**Concern:**

The contract specifies that the session is stored in IndexedDB client-side (M1 requirement), and the ADR says the client is the source of truth for this user. But if Jamie has two devices, and one of them has an older IndexedDB snapshot, the client-first architecture creates a conflict: which client is the source of truth? The current contract and ADR do not address multi-device reconciliation (deferred to M2). However, the stories (Maya, Kenji, Jamie) all imply single-device usage, and Jamie's story specifically covers hours-long gaps that might allow server updates. The silent wrongness occurs because Jamie's app will quietly show the stale state without warning, and Jamie may not realize the session is actually complete on the server.

**Property:**

For all sessions restored from IndexedDB, the session's state (`pending`, `completed`, `extended`) must match the server's canonical state, or the app must explicitly signal the divergence to the user. Stale state is only acceptable if the user knows it's stale.

**Implies:**

- Implies architectural decision: how do we handle client-server divergence in M1? The current ADR says client is source of truth, but doesn't address the case where the client is out of date. This assumes single-device usage; if Jamie is using the app on multiple devices, we need a sync strategy. Flag for Cheshire Cat.
- Implies Kenji/Tweedledum backend responsibility: need a sync-on-reopen endpoint that returns the canonical state for any session the client asks about, so stale IndexedDB can be detected. The endpoint should at least return the current state of any session by ID.
- Implies Alice: clarify whether Jamie's story assumes single-device usage or whether multi-device scenarios are in scope for M1.

