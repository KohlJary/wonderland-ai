## Scenario: Registration — concurrent signup race on same username

**Severity:** breakage

**Setup:**

Two registration requests arrive simultaneously, both claiming the same desired_username "jordan". Neither has been verified yet. The system's uniqueness constraint on username is in place, but the check-then-insert window is not atomic.

**Trigger:**

Both requests pass email validation, enter the uniqueness check concurrently, both see "username available", then both attempt INSERT. Depending on DB isolation and transaction handling, one succeeds and one fails—but which one? And what does the failure message reveal?

**Expected:**

Exactly one registration succeeds. The second receives a clear error: { error: "username_taken", suggested_usernames: ["jordan2", "jordan_music", ...] }. Both users can retry immediately. No silent data corruption (e.g., both users think they won, one finds their account inaccessible).

**Concern:**

SQLite (the test DB) is single-threaded and serializes by default, so this passes locally. But the production deployment may use PostgreSQL or MySQL, which do allow concurrent transactions. If the team doesn't use database-level uniqueness constraints + optimistic locking or explicit transactions, this race is a silent failure: user A believes they signed up, but user B's INSERT succeeds and overwrites. Or: no unique constraint at all, both INSERTs succeed, and lookups are now ambiguous.

**Property:**

For all users U1, U2 attempting registration with username U in the same instant: at most one succeeds with status 200/verified-pending; the other receives a 409 (conflict) or 422 (validation) with suggested alternatives. The system maintains username uniqueness as an invariant.

**Implies:**

Implies database schema decision (unique constraint on username column + appropriate index) — flag for Caterpillar on schema review. Implies contract clarification: does POST /register enforce uniqueness synchronously (user sees error immediately) or asynchronously (user gets a token that becomes invalid if username is stolen)? Current contract assumes synchronous, which requires locking.

---

## Notes for Test Implementation

The pytest test will:
1. Set up two "simultaneous" requests using concurrent.futures or threading.
2. Both attempt POST /register with same username.
3. Assert exactly one succeeds (or both fail with expected errors).
4. Verify suggested_usernames are returned when username is taken.
5. Verify both can immediately retry with different usernames.

This test will FAIL until the backend implements proper uniqueness handling.
