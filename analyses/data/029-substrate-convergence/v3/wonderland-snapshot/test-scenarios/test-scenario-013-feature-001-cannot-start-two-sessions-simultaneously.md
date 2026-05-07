## Test Scenario 013: Cannot start a second session while one is already running

**Severity:** breakage

**Feature:** Feature 001: Run a focused work session with built-in break

**Setup:**

Marcus has started a 25-minute session. The Session record exists in the DB with status=running, started_at=T0. The frontend is displaying the countdown.

**Trigger:**

For some reason, Marcus taps the Start button again (or the frontend's optimistic retry fires twice due to a network hiccup). The backend receives two POST /api/session/start requests in rapid succession.

**Expected:**

- First request: creates a Session with status=running. Response 200 OK.
- Second request: returns 409 Conflict (or similar). Error message: "A session is already in progress. Complete or abandon it before starting a new one."
- The DB contains exactly one Session record with status=running.
- No duplicate sessions are created.

**Concern:**

If the backend doesn't enforce the "only one active session" invariant, two Session records could be created, both with status=running. This breaks the state machine. When the first session's timer reaches zero, the backend might complete both sessions, or only one, or crash trying to figure out which one to complete. History queries will show duplicate sessions. The user's daily count will be wrong.

**Property:**

For all time periods T, count(Session records where status != 'completed') <= 1. At most one session is active at any moment.

**Implies:**

This tests backend state machine enforcement at the DB schema level. Requires a database constraint (UNIQUE index on (status='running')) or application-level validation before write. The contract note specifies this invariant; the test validates it.

