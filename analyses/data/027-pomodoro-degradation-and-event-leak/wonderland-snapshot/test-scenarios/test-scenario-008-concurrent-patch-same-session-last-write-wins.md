## Scenario: Two PATCHes to the same session arrive concurrently; last write wins without error

**Severity:** silent-wrongness

**Setup:**
A session with id='abc123' is in progress with completionStatus='pending'. Session is open in two browser tabs on the same machine (or two devices, both logged in as the same user in M1 single-user model). Both tabs have the session visible and a timer counting down.

Real time: session is 20 minutes in. Remaining time: 5 minutes.

**Trigger:**
Tab 1: User taps "Mark Complete" at 24:50 (10 seconds remaining). Sends PATCH /sessions/abc123 with {completionStatus: 'completed', actualDuration: 20}.

Tab 2: User taps "Mark Complete" at 24:55 (5 seconds remaining). Sends PATCH /sessions/abc123 with {completionStatus: 'completed', actualDuration: 25}.

Both requests arrive at the backend within milliseconds of each other. The order is Tab 2's PATCH arrives *after* Tab 1's PATCH (but they might be processed in either order due to network jitter or server queueing).

**Expected (per ADR-002, M1 constraint):**
No error is returned to either tab. Both PATCHes succeed (200 OK). The session's final state is determined by whichever PATCH wins (last-write-wins). In this case, Tab 2's value wins: actualDuration=25. Both tabs eventually converge to the final state (either via polling or by re-reading after the PATCH response).

**NOT expected:**
- HTTP 409 Conflict returned to one of the clients (that would imply optimistic locking, which adds complexity for M1)
- One PATCH rejected while the other succeeds (that would imply strict serialization, which also adds complexity)
- Partial update (actualDuration becomes 25 but completionStatus stays 'pending')
- Race condition where both values are merged (e.g., actualDuration=[20, 25])

**Concern:**
The backend might use a READ-MODIFY-WRITE pattern without any concurrency control:
1. Tab 1 PATCH arrives: read session (status=pending, actualDuration=null), write {status=completed, actualDuration=20}
2. Tab 2 PATCH arrives: read session (status=completed, actualDuration=20), write {status=completed, actualDuration=25}

If there's a race between 1 and 2 (a window where Tab 1's write isn't yet flushed to storage when Tab 2 reads), Tab 2's write might overwrite Tab 1's, which is correct for last-write-wins.

But if there's no protection at all, and the reads/writes are not atomic, the session might end up in a corrupted state:
- Both PATCHes read the same baseline state
- Both apply their delta
- Both write, and the second write overwrites the first
- The session ends up with actualDuration=25 (correct)

...OR:
- Both PATCHes execute in parallel on the database
- The UPDATE statements race
- The database gets confused about the final state

For last-write-wins to be *reliable*, the backend needs either:
- A timestamp or version field on the session that gets incremented with each update (and ignored during merge — just the field values are used, not the version)
- Or: a sequence of update-is-a-full-replace (so the second PATCH fully replaces the first, no merging)

The silent wrongness: the implementation might achieve last-write-wins *by accident* (because of database-level optimizations) but without explicit handling, a future change breaks it. Or the implementation might fail under load (high concurrency from other users) even though M1 is single-user and testing never sees the race.

**Property:**
For all concurrent writes to the same session (from different tabs/devices):
- Both writes are accepted (no 409 Conflict)
- The final state of the session is the state specified by whichever write happened last (chronologically, wall-clock time)
- No partial updates (all fields of the PATCH are applied together)
- No data loss or corruption (actualDuration and completionStatus are both updated, not just one)
- Client is not required to handle optimistic-locking errors or merges

**Implies:**
- Implies concurrency strategy: last-write-wins via full replacement or version-based resolution. Flag for Tweedledum.
- Implies idempotency: if Tab 1 sends the same PATCH twice (due to perceived network failure), the second PATCH should be idempotent — actualDuration remains 20, not doubled or merged. This requires either request deduplication or a timestamp-based conflict resolution. Flag for contract review.
- Implies testing: M1 single-user doesn't require high-concurrency testing, but the behavior should be documented and tested at least at the 2-concurrent-write level. Flag for Tweedledee's test suite.
- Implies UI: if a user has two tabs open and both are updating the session, the UI in each tab needs to eventually converge to the final state. This might require polling or a WebSocket subscription. Deferred to later contract for multi-user; M1 can assume user won't open two tabs. Flag for Tweedledee.
