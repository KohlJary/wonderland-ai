## Scenario: Session start succeeds during concurrent config patch; session uses new or old length, consistently

**Severity:** degradation

**Setup:**

User's session config is set to 25 minutes. User is about to start a session. Simultaneously, the client is sending `PATCH /config` to change `session_length_minutes` from 25 to 50. Both requests hit the backend within the same 100ms window — true race condition.

**Trigger:**

`POST /sessions/start` and `PATCH /config` race. Either the start reads config before the patch, or after the patch, but not during.

**Expected:**

Either:
1. Session starts with 25 min (PATCH applies after start reads config), or
2. Session starts with 50 min (PATCH applies before start reads config).

The choice is deterministic given the execution order. The session's `target_duration_seconds` is consistent with the config value it read: if it read 25, target is 1500; if it read 50, target is 3000.

**Concern:**

Without transaction isolation, the session's `target_duration_seconds` may read a config value mid-update, causing a mismatch. For example:
- Backend starts reading config.session_length_minutes (gets 25)
- PATCH /config runs, sets session_length_minutes to 50
- Backend finishes reading, but now config has changed
- Session is created with target_duration_seconds = 50 * 60 = 3000, but the config value is now 50

Result: session's target duration matches current config, but there's a silent inconsistency if the client expected 25.

Even worse: the backend might read config.session_length_minutes = 50, then the PATCH applies a different change (e.g., break_length), and the session ends up with a config value that was never explicitly requested (race condition leak).

**Property:**

For all concurrent starts S and config-patches P:
- Either S reads the config strictly before P begins, or strictly after P completes. No partial reads.
- The invariant holds: `session.target_duration_seconds == config.session_length_minutes * 60` at the moment the session is returned.

**Implies:**

- Implies backend must use transaction isolation (at least serializable or repeatable-read) to ensure consistent snapshot reads of config.
- Implies SQLite's default autocommit mode may be insufficient; may need explicit transaction boundaries or SQLAlchemy's isolation-level settings.
- Implies test harness needs concurrency primitives (e.g., threading with controlled timing, or asyncio with yield points) to deterministically trigger the race. Current in-memory SQLite test client is single-threaded.
