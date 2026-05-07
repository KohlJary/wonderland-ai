## Test Scenario: Concurrent start-session requests from same session_id create race condition

**Severity:** silent-wrongness

**Feature:** Feature 001: Run a focus session with breaks

**Setup:**

User has session_id=abc-123. Frontend is flaky; POST /sessions/start is retried twice in rapid succession before the first response arrives.

**Trigger:**

Two concurrent requests both start phase transition logic simultaneously.

**Expected:**

Backend serializes or deduplicates: either the second request sees current_session already exists and returns conflict, or first request completes fully before second can execute.

**Concern:**

If backend naively sets current_session = new_session without locking or check-then-act, two threads may both create new sessions. Then when first one completes and writes to DB, the second one hasn't recorded its phase and elapsed_time—data loss or inconsistency.

**Property:**

For all concurrent start-session requests on the same session_id S, exactly one current_session is created or an error is returned; never two.

**Implications:**

- Backend concurrency model — Tweedledum needs to decide: thread-safe counter, async lock, or DB-level uniqueness constraint.
