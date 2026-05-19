## Scenario 276: localStorage lastSyncedAt is newer than server updated_at (clock drift or time-travel)

**GUID:** 01KRY19Z4NS2MZ90DE1K35D5GG
**Severity:** degradation

**Setup:**

User's device has a clock that's set ahead by 10 minutes. They edit a note locally and save it at 3:50 PM (device time), which gets persisted on the server with server timestamp 3:40 PM (actual time). Later that day, user edits the same note again and refreshes the page. localStorage has {lastSyncedAt: '2026-05-18T15:50:00Z', ...}. Server's note has updated_at: '2026-05-18T15:40:00Z'.

**Trigger:**

App boots and compares localStorage.lastSyncedAt against server.updated_at for the same note.

**Expected:**

The contract (contract-note-01KRXXCX) says: 'if localStorage.lastSyncedAt < server.updated_at, show Restore button + Discard button; if timestamps match, silently discard it.' In this case, lastSyncedAt > updated_at (due to clock drift), which the contract doesn't address. Expected behavior: log a warning (clock drift detected), and use updated_at as the source of truth (discard the stale localStorage).

**Concern:**

The contract assumes clock-monotonicity (localStorage was synced at server time X, so localStorage's lastSyncedAt <= server's updated_at). But if the device clock is wrong, localStorage.lastSyncedAt might be ahead of server.updated_at, breaking the comparison logic. This is rare, but it's a silent wrongness case: the code compares timestamps, finds no match, and defaults to an incorrect choice (keeping localStorage when the server is actually newer).

**Property:**

For all cases where localStorage.lastSyncedAt is compared to server.updated_at: if localStorage.lastSyncedAt > server.updated_at, log a warning and discard localStorage (treat server as authoritative). Clock drift is a signal that the device clock is wrong, not that localStorage is newer.

**Implies:**
- Implies backend contract refinement: server response should include a server timestamp (generated at response time, not at update time) so client can calibrate its local clock. Or contract explicitly states lastSyncedAt < server.updated_at is assumed, with documented clock-drift behavior.
