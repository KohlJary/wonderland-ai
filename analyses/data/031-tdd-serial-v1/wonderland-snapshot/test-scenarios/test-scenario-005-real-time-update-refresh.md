## Scenario: User views daily review, completes a session, stats update without page reload

**Severity:** degradation

**Setup:**

David opens the daily review screen at 10am. It shows 2 completed focus sessions, 50 minutes.

David then completes a third focus session (25 minutes) while looking at the daily review screen.

**Trigger:**

The third session completion event is logged to the backend.

**Expected:**

Within 5 seconds (frontend polling interval or WebSocket delivery), the daily review screen updates to show:
- 3 completed focus sessions
- 75 minutes total

The user sees this without pressing "refresh" or reloading the page.

**Concern:**

If the frontend only fetches stats on page load, the review is always stale. The contract note mentions "real-time updates: frontend polls or WebSocket-subscribes" but doesn't specify which. If neither is implemented, the user sees yesterday's stats until they refresh.

This is degradation, not breakage — the feature still works, it's just not real-time. But it's a core part of the user story: "I want to see my performance *as I'm working*" implies live updates.

**Property:**

For all completion events E logged at time T:
- Any frontend client with daily review open must receive the aggregated update by time T+polling_interval (or T+network_latency if WebSocket)
- The update must reflect E in the query results before the user manually refreshes

**Implies:**

- Implies contract decision: polling vs. WebSocket? Polling interval if polling?
- Implies backend API: need an endpoint for frontend to poll, or WebSocket support
- Implies frontend code: polling loop or WebSocket listener that updates stats
- Implies test structure: mock time or integration test with actual polling
