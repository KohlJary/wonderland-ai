## Test Scenario 021: Historical data is ordered newest-first, not oldest-first

**Severity:** degradation

**Feature:** Feature 003: Inspect historical session data across weeks and all-time

**Setup:**

Yuki has completed sessions on:
- Jan 10: 2 sessions, 50 minutes
- Jan 12: 3 sessions, 75 minutes
- Jan 15 (today): 1 session, 25 minutes

She opens the "This Week" view to see her progress. The expected order is:
- Index 0: Jan 15 (today, newest)
- Index 1: Jan 12
- Index 2: Jan 10 (oldest in the 7-day window)

**Trigger:**

The app fetches GET /api/session-history/weekly and renders the list.

**Expected:**

The list displays in newest-first order (Jan 15 at the top, Jan 10 at the bottom). This matches the typical mobile UX expectation where "today" is at the top and the user scrolls down to see older days.

**Concern:**

If the backend returns the data in oldest-first order (Jan 10 at the top), the frontend will show a confusing view: the user has to scroll all the way down to see today's data. Over multiple sessions, users might not notice the order is backwards and might misinterpret their productivity trends.

Alternatively, if the backend doesn't specify the order and different backends/languages sort differently, the frontend might receive data in inconsistent orders, breaking the assumption that today is always at the top.

**Property:**

For all historical aggregation responses, data is sorted by date DESC (newest first). The date at index 0 is >= the date at any subsequent index.

**Implies:**

This tests the sorting in the backend's historical queries (contract-note-006 specifies ORDER BY completed_at DESC). The scenario validates that the frontend can assume newest-first ordering without additional sorting logic.

