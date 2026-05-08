## Scenario 014: Skip a break and immediately start new focus — no ghost session

**Severity:** silent-wrongness

**Setup:**

Break timer is running (status='running'). User taps skip, and within 50ms taps 'start new focus session'.

**Trigger:**

Two rapid API calls: (1) POST /api/sessions/<break_id>/skip, (2) POST /api/sessions/start with duration_seconds=1500.

**Expected:**

Both succeed. Break transitions to completed, new focus is created independently. User's UI shows new focus, not the skipped break. No lingering break session with status='running'.

**Concern:**

Race condition: if skip is not atomic, the backend might return the break as 'still running' to a concurrent start request. Client might see multiple active sessions. Silent wrongness: API returns correct data, but accumulated state corrupts the view.

**Property:**

Only one session with status='running' exists at any moment. Previous sessions all have status='completed'.
