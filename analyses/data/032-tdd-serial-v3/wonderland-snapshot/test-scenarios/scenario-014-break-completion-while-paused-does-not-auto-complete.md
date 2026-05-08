## Scenario 014: Break completion while paused does not auto-complete

**Severity:** silent-wrongness

**Setup:**

Break timer is running. Keisha pauses it.

**Trigger:**

Due to a scheduler glitch or test artifact, the timer's 'completion at 0 seconds' event still fires while the session is paused.

**Expected:**

Session status remains 'paused' (not 'completed'). No notification fires to Keisha until she explicitly resumes or skips.

**Concern:**

If the backend transitions the session to 'completed' whenever a completion event fires, it will ignore the paused state. The UI shows paused; the backend shows completed. Keisha resumes, and the app is confused.

**Property:**

Completion events should only transition status from 'running' to 'completed', never from 'paused' to 'completed'.

**Implies:**
- Backend-side: completion handler must check status before transitioning. Only 'running' -> 'completed' is valid. 'paused' -> 'completed' should be rejected or ignored.
