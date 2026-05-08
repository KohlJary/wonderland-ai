## Scenario 002: Marcus pauses mid-session and resumes without losing elapsed time

**Severity:** breakage

**Setup:**

A focus session is running. Marcus has been focused for ~10 minutes. The timer displays 15 minutes remaining.

**Trigger:**

Marcus taps 'Pause'. Sixty seconds pass. Marcus taps 'Resume'.

**Expected:**

When paused, countdown stops and remaining time stays frozen at ~15 minutes. When resumed, countdown continues from that point.

**Concern:**

Pause/resume is an explicit acceptance criterion (Story 001). If time is lost during pause, Marcus loses trust. If pause doesn't work, he can't protect focus sessions.

**Property:**

When a session is paused, elapsed_time does not advance. When resumed, elapsed_time continues from the pause point without reset.

**Implies:**
- Requires pause/resume state handling — **contract-001 must finalize pause interface (endpoint? client-side state?)**
- Requires frontend to respect pause in countdown display.
