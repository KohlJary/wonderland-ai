## Scenario 001: Marcus starts a 25-minute focus session and watches the countdown

**Severity:** breakage

**Setup:**

Marcus opens the app. No running session. The focus-session screen shows a 'Start Focus' button.

**Trigger:**

Marcus taps 'Start Focus'.

**Expected:**

A 25-minute timer begins counting down. The UI displays remaining time (25:00, 24:59, 24:58...) and updates every second. After 25 minutes, the session completes and a notification fires.

**Concern:**

The timer is the core feature. If it doesn't start or count down, Marcus won't use the app. This is the foundational test.

**Property:**

For any focus session with initial duration D seconds, remaining_time = D - elapsed_time, and remaining_time >= 0 until the session is marked completed.

**Implies:**
- Requires backend session creation (implied by contract-005 POST /sessions/log).
- Requires completion notification to fire per contract-005.
