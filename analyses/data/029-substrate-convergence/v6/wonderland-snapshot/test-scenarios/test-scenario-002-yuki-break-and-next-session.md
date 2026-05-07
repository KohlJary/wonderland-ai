## Test Scenario: Yuki Completes a Break and Starts the Next Session

**Severity:** breakage (if this fails, the core pomodoro cycle is broken)

**Setup:**

Yuki is a 34-year-old manager who is rigorous about breaks. She has just completed her first 25-minute focus session. The app has notified her. She has 5 minutes to step away. The break timer is active.

**Trigger:**

The break timer counts down from 5:00. When it expires, Yuki sees a notification. She then taps "Start Next Session" (or the app displays a ready-to-start state). She starts session 2.

**Expected:**

1. After session 1 completes, the system automatically transitions to a break state (or the next start is simply available)
2. GET /sessions/today now shows 1 completed session
3. The user can POST /sessions/start to begin session 2
4. Session 2 starts with is_active=true and target_duration=1500 (default)
5. GET /sessions/today now shows 2 completed sessions (the old one) and implicitly that a new session is active
6. After session 2 completes, GET /sessions/today shows summary.count=2

**Concern:**

The concern is that:
- The break timer might not work (if it's a separate entity, it might not be implemented)
- Multiple active sessions might be allowed (violating the invariant)
- The transition from session → break → session might lose data or corrupt state
- The config (break_length_minutes) might not be respected, using global default instead

**Property:**

For all users U with config C:
- After session S1 completes (is_completed=true), user can start S2 without error
- At most one session at a time is active (is_active=true)
- GET /sessions/today after S2 completes shows summary.count >= 2

**Implies:**

- Implies break state management (could be separate Break entity or implicit in Session flow)
- Implies config must be fetched and respected at session-start time
- Implies state-machine invariant: only one active session per user
