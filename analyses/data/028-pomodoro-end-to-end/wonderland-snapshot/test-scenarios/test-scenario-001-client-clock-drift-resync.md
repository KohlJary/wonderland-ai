# Test Scenario 001: Client Clock Drift and Server Time Authority

**Severity:** silent-wrongness

**Feature:** Feature 001 (Start a focus session and get notified when it ends)

**Contract:** Session lifecycle & timer state

**Setup:**
Marcus starts a 25-minute focus session. His client receives the response:
```json
{
  "id": "sess-123",
  "state": "active",
  "start_time": "2024-01-15T10:00:00Z",
  "duration_minutes": 25,
  "remaining_seconds": 1500
}
```
Client caches `{start_time, remaining_seconds}`.

The user's device clock is 8 seconds fast relative to the server. On the client:
- Actual time: 10:00:05 (8 seconds ahead of server's 9:59:57)
- Cached remaining: 1500

**Trigger:**
Client computes local elapsed via: `elapsed = (now_client - cached_start_time)`

Then computes remaining locally: `remaining = cached_remaining - elapsed`

At client time 10:00:08 (server time 10:00:00):
- Client elapsed: 8 seconds
- Client remaining: 1500 - 8 = 1492 seconds
- But server, polling at 10:00:00, computes remaining: 1500 - 0 = 1500 seconds (different!)

**Expected:**
Client polls `/session/current` at 10:00:08 (server time 10:00:00). Server returns:
```json
{
  "remaining_seconds": 1500,
  "elapsed_seconds": 0,
  "start_time": "2024-01-15T10:00:00Z"
}
```

Client detects drift: |client_remaining - server_remaining| = |1492 - 1500| = 8 > 5s

Client resyncs to server value. Display shows 1500 remaining (server truth), not 1492 (client lie).

**Concern:**
If client naively trusts local clock math without syncing, the timer display drifts further from server truth with each local computation. After 100 client polls with no resync, the client display could be minutes off from reality.

User sees: "4:30 remaining" (client computation)
Server says: "4:22 remaining" (server truth)

Silent wrongness: the UI appears correct (it's counting down) but is untethered from reality. When user sets a goal ("I'll complete X by 4:30 server time"), the display lies.

**Property:**
For all polls of `/session/current`, if `(client_remaining - server_remaining) > 5 seconds`, client must resync to `server_remaining` on the next response.

**Test File:** `tests/test_feature_001_timer_authority.py::test_client_drift_greater_than_5_seconds_triggers_resync`

**Implies:**
- Frontend implementation detail (Tweedledee's concern): client timer reconciliation logic.
- Not a backend failure, but a frontend requirement in the contract.
