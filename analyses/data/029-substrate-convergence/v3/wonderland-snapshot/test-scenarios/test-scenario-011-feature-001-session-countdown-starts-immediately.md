## Test Scenario 011: Session countdown starts immediately, no lag

**Severity:** degradation

**Feature:** Feature 001: Run a focused work session with built-in break

**Setup:**

Marcus has the app open on his phone. The timer is idle, showing the start button. He has the default settings (25 min session, 5 min break) configured.

**Trigger:**

Marcus taps the "Start Session" button. The request hits the backend, which creates a Session record with status=running and records the current server time as started_at.

**Expected:**

The frontend countdown begins within 100ms of the button tap. The first visible tick should show 24:59 or 24:58 (within 1 second of the actual elapsed time). Subsequent ticks are accurate to within 1 second per update.

**Concern:**

If the frontend waits for the backend to respond before starting the local timer, there's a 200-500ms network delay. Users perceive this as lag — the button feels unresponsive. Instead, the frontend should immediately start a local timer and reconcile with the server's started_at when the response arrives.

**Property:**

For all session starts, time_perceived_lag = response_time + (response_time > 100ms ? response_time : 0). The frontend should never wait for the backend to begin countdown; it should be optimistic.

**Implies:**

This is a frontend UI responsiveness issue, not a backend contract issue. The contract already supports this (started_at is sent immediately). This is a testing seam between frontend timing behavior and backend state.

