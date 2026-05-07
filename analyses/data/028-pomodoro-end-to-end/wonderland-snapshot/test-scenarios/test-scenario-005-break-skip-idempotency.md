## Scenario: Priya taps Skip Break twice (network hiccup); the second tap is a no-op

**Severity:** silent-wrongness

**Setup:**
Break is active, showing 4:30 remaining. Priya is ready to start her next task; she taps the "Skip Break" button.

**Trigger:**
First tap: POST /break/skip request sent, reaches server, break→skipped transition happens, response is in-flight back to client.
Meanwhile: Network hiccup, client doesn't receive response, UI remains in "skip in-flight" state.
User re-taps: POST /break/skip request sent again.

**Expected:**
1. First skip: break transitions to state=skipped, /break/current returns {state: skipped}
2. Second skip: same request returns 200 with {state: skipped}, NOT creating a new break or reverting skip
3. Client sees identical response to both requests (idempotent)

**Concern:**
If skip is not idempotent:
- Second skip might create a new break record or revert state to active
- Break state becomes ambiguous: is it skipped or active?
- User can't reliably start the next session because the system disagrees with what state the break is in
- Silent wrongness: the app appears to work but the data is inconsistent

This violates the invariant "skip is idempotent and final."

**Property:**
For any active break B:
- POST /break/skip → {state: skipped}
- POST /break/skip (issued again) → {state: skipped} (same result, no side effects)
- Once break→skipped, it cannot transition back to active

**Implies:**
- Implies backend: skip endpoint must be idempotent (either stateless or checking current state before updating)
