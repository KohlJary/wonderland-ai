## Scenario: Sessions created at 11:59 PM and 12:00 AM are correctly separated by day boundary

**Severity:** silent-wrongness

**Setup:**

User's timezone is UTC. Three sessions, created at specific times:
1. 2024-11-15 11:59:50 UTC — session is created and completed immediately (duration ~1 second).
2. 2024-11-15 23:59:59 UTC — session is created and completed immediately (duration ~1 second).
3. 2024-11-16 00:00:01 UTC — session is created and completed immediately (duration ~1 second).

Frontend queries `GET /sessions/range?start_date=2024-11-15&end_date=2024-11-15` expecting only sessions 1 and 2 (both completed on Nov 15).

**Trigger:**

`GET /sessions/range` with date boundaries that should exclude session 3.

**Expected:**

Response includes only sessions 1 and 2. Session 3 (created after midnight on Nov 16) is NOT included in the Nov 15 range.

**Concern:**

Date-boundary logic may be naive about UTC conversion or local-time interpretation. Common issues:
- Backend might use `datetime.now().date()` instead of `datetime.now(timezone.utc).date()`, causing boundary shifts based on server time.
- Backend might include the entire UTC day (00:00:00 to 23:59:59 UTC) instead of the local-day window.
- Backend might use `>=` for the end date instead of `<=`, causing the next day's sessions to leak into the range.

Result: session 3 appears in the Nov 15 results even though it was created on Nov 16. Silent wrongness (user sees inflated session counts for Nov 15).

**Property:**

For all sessions S and queries Q with date range [D1, D2]:
- S is included in Q's result iff `S.start_time` falls within `[D1 00:00:00, D2 23:59:59]` in the user's configured timezone, converted to UTC for comparison.
- No sessions from other days "bleed" into the range due to timezone offset or boundary arithmetic.

**Implies:**

- Implies backend's `get_sessions_range` function must:
  1. Parse the ISO8601 date strings (e.g., "2024-11-15").
  2. Convert them to the user's timezone (e.g., UTC).
  3. Create UTC timestamps: `[D1 00:00:00 UTC, D2 23:59:59 UTC]`.
  4. Query sessions where `start_time >= D1_UTC AND start_time <= D2_UTC`.
- For now, Tweedledum's backend assumes UTC and doesn't use the user's configured `timezone` field. This works for UTC users but will fail when timezone support is added. Test should pass today but may need updates in future.
- Implies test harness could use freezegun or time-mocking to create sessions near midnight without waiting for real midnight. Current tests create sessions in rapid succession; Tweedledee's code doesn't mock time, so this test will pass by accident (all sessions created in the same second).

**Note:** This scenario is a pre-check for future multi-timezone support. For v1 (UTC-only), the boundary should work correctly. If timezone configuration is added in v2, this scenario becomes critical.
