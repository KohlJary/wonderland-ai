## Contract Note 006: Historical sessions query: date range and aggregation

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

undefined

**Proposed Change:**

Define GET /sessions/range?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD. Returns sessions for that range. Optionally support aggregation endpoint GET /sessions/stats/range?start_date=...&end_date=... for charts (total sessions, total time, per-day breakdown).

**Source:** Feature 004.

**Frontend Impact (Tweedledee):**

Frontend handles date picker, submits range query. For v1, assume no charts; just list view. Stats endpoint can be v2 fast-follow. Client-side pagination if result set is large (100+ sessions).

**Backend Impact (Tweedledum):**

GET /sessions/range?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD returns all is_completed=true sessions for user in that range. Ordered by start_time DESC. Pagination: default 50 per page, supports ?page=N&limit=M (cap limit at 500). Stats aggregation (total sessions, total seconds, per-day breakdown) is v1.1 — for v1, just return raw list. Query indexed on (user_id, created_at) for speed. Client-side pagination is fine for v1 (max ~1500 sessions/year = manageable).
