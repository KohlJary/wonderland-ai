## Test Scenario 016: Session completed just before midnight is counted in today, not tomorrow

**Severity:** silent-wrongness

**Feature:** Feature 002: Review today's session count

**Setup:**

Maya completes a session at 11:59 PM on January 15th. The session's completed_at timestamp in the DB is 2025-01-15T23:59:00Z. She looks at the "Today" view, which correctly shows count=1.

**Trigger:**

The system clock advances to 12:01 AM on January 16th. Maya opens the app (or the frontend detects the midnight crossing). The app fetches GET /api/session-counts/today.

**Expected:**

The count should return count=0 (and maybe show "No sessions yet" or "Start your first session").

The session completed at 11:59 PM on the 15th should NOT be included in today's (the 16th) count. It should only appear in historical views under "January 15th."

**Concern:**

If the backend's "today" boundary is not strictly at midnight (e.g., if it's calculated relative to the user's local timezone but the backend runs in UTC), or if the frontend's cache invalidation doesn't trigger at midnight, the user might see stale data. They might see the session from 11:59 PM on the 15th still counted in today's (16th) count, which is wrong.

Also, if the frontend doesn't detect the midnight crossing and doesn't invalidate its cache, the count will remain stale until the user manually refreshes.

**Property:**

For all sessions S and times T:
- If S.completed_at is on date D and T is on date D, then S is included in daily_count(T).
- If S.completed_at is on date D and T is on date D+1 or later, then S is NOT included in daily_count(T).
- Midnight UTC is the boundary (v1 limitation; full timezone support is post-v1).

**Implies:**

This tests the boundary between "today" and "yesterday" at the backend query level (contract-note-004) and the frontend's cache invalidation at midnight.

