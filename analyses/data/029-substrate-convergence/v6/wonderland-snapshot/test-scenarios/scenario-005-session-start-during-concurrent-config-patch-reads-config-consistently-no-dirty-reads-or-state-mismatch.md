## Scenario 005: Session start during concurrent config patch reads config consistently; no dirty reads or state mismatch

**Severity:** degradation

**Setup:**

User's config is 25 min session, 5 min break. User starts session while simultaneously sending PATCH /config to change session_length to 50 min. Both requests hit backend within 100ms.

**Trigger:**

POST /sessions/start and PATCH /config race; start must read config atomically.

**Expected:**

Either start reads config before patch (session targets 1500 sec) or after patch (session targets 3000 sec). No partial reads. Session's target_duration_seconds is consistent with config it read.

**Concern:**

Without transaction isolation, start might read session_length_minutes mid-patch, reading partially-updated config or reading one field before and another after patch. Result: session target duration doesn't match config it read.

**Property:**

For all concurrent starts S and config-patches P, S reads config at single consistent snapshot. session.target_duration_seconds == config.session_length_minutes * 60 at moment of return.

**Implies:**
- Implies backend must use transaction isolation (repeatable-read or serializable) to ensure consistent snapshot reads.
- Implies test harness needs concurrency primitives (threading or asyncio with tight timing) to trigger race deterministically.
