## Scenario 008: Session created at 23:59:59 UTC included in today's range; session created at 00:00:01 next day excluded

**Severity:** silent-wrongness

**Setup:**

UTC timezone. Three sessions: (1) 2024-11-15 11:59:50 completed, (2) 2024-11-15 23:59:59 completed, (3) 2024-11-16 00:00:01 completed. Query GET /sessions/range?start_date=2024-11-15&end_date=2024-11-15.

**Trigger:**

Date-boundary query; must correctly exclude next-day sessions.

**Expected:**

Response includes only sessions 1 and 2 (both on Nov 15). Session 3 (Nov 16) excluded.

**Concern:**

Date-boundary arithmetic may be naive: might use >= for end_date instead of <=, or use server local time instead of UTC, or include entire UTC day instead of local-day window. Sessions from next day can leak into range.

**Property:**

For all sessions S and queries Q with range [D1, D2], S included iff S.start_time within [D1 00:00:00, D2 23:59:59] in user's timezone, converted to UTC for comparison.

**Implies:**
- Implies backend date parsing and filtering must be timezone-aware. For v1 (UTC-only), works; for multi-timezone v2, critical.
- Implies test harness could use time-mocking (freezegun) to create sessions near midnight without waiting for real midnight.
