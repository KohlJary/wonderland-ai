## Scenario 008: Keisha sets break duration and it starts automatically when focus ends

**Severity:** breakage

**Setup:**

Keisha has launched the app. No session is running. Break duration is at default (300 seconds).

**Trigger:**

Keisha sets break duration to 600 seconds via settings UI. Focus session starts and runs to completion. Timer should transition to break timer.

**Expected:**

Break timer starts automatically, showing 600 seconds remaining. The timer counts down at the correct rate (1 second per second). When 0 is reached, session marks as completed.

**Concern:**

The contracts don't explicitly say when the break timer starts: immediately when focus completes, or only after the user acknowledges a notification? Also, is the break session created in the backend (via POST /sessions/log), or is it ephemeral client-side until completion? Keisha's story implies seamless auto-start, so I'm assuming: (1) Focus completion immediately triggers break timer on client, (2) Break completion POSTs to /sessions/log once (idempotent). But if backend needs to create the break session first, there's a race.

**Property:**

For all break durations D in [60, 1800] seconds, if a focus session completes and break_duration_seconds = D, then the break timer's remaining_seconds should be in range [D - 1, D] (allowing 1 second clock drift).

**Implies:**
- Depends on Contract-002 (settings storage) — frontend must read break_duration_seconds from localStorage and apply to next session.
- Depends on Contract-001 (session model) — backend must accept POST /sessions/log for break sessions with type='break'.
- Depends on Contract-003 (session completion event) — frontend must POST when break timer reaches 0.
