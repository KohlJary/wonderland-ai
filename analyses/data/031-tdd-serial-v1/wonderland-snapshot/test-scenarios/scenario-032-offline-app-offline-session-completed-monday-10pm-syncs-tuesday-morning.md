## Scenario 032: Offline: app offline, session completed Monday 10pm, syncs Tuesday morning

**Severity:** degradation

**Setup:**

Derek's phone offline Monday evening. Completes session at Mon 10pm (logged locally). Offline overnight. Tuesday morning: syncs.

**Trigger:**

Sync uploads Monday session. Streak query runs.

**Expected:**

Session attributed to Monday (completion_timestamp wins, not sync_time). Monday's streak includes this session.

**Concern:**

If system uses sync_time instead of completion_time, Mon session counted as Tue. Streak might break incorrectly.

**Property:**

Offline session timestamp (local-device-time) is canonical. Sync-to-backend time irrelevant for streak.

**Implies:**
- Implies Feature 003: offline queue + sync with completion_timestamp preserved
- Implies backend: sessions have completion_timestamp that survives sync
