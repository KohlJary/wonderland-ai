## Scenario: User taps 'Extend' within the last 5 seconds of focus time; extension is honored

**Severity:** silent-wrongness

**Setup:**
A focus session is in progress with targetDuration=25 minutes. Real time has advanced 24 minutes 55 seconds (5 seconds remaining). Session is not yet marked completed. User can observe the countdown timer.

**Trigger:**
User taps an 'Extend Session' button or action. The extension adds 5 more minutes to the remaining time.

**Expected:**
The timer does NOT complete. The session's countdown extends to 5 additional minutes (timer shows 5:00 or the countdown continues past 0:00). The completion notification does NOT fire. After the extended time elapses (5 more minutes), the session completes with completionStatus='completed' and actualDuration=30.

**Concern:**
This is a race condition. If the client's timer fires at second 25.0 AND the user taps 'extend' at second 24.999, both events might fire. The notification fires, the extension PATCH is in flight, and the user sees contradictory state (session marked completed + timer still running). Alternatively, the PATCH request to extend might be in flight when the local timer fires, and the client might transition to 'completed' before the server sees the extension. When the PATCH response arrives, the server might reject it (session already completed) or the client might ignore the response (already showed completion notification). The session's actualDuration might be 25 instead of 30, silently losing the extension time.

**Property:**
For all extension operations: the most recent (chronologically last) operation must win. If a user taps 'extend' within 1 second of natural completion (clock-wise, not event-wise), the extension must be honored and the completion notification must not fire. Repeated identical extension requests must be idempotent (second tap does not grant 2 extensions).

**Implies:**
- Implies optimistic-update / offline-first pattern: client-side timer must not fire if an extension PATCH is in flight. Needs deferred completion or extension confirmation flow. Flag for Tweedledee.
- Implies contract precision: does targetDuration change on extend (new contract field added), or does actualDuration include the extension? If targetDuration is immutable, how is the extension time stored? Flag for Tweedledum and contract review.
- Implies atomicity: the session update (targetDuration or extended time + actualDuration) must be atomic. Partial updates corrupt the record. Flag for Tweedledum.
