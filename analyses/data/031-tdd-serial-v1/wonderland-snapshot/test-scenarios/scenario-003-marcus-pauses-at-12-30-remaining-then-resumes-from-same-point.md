## Scenario 003: Marcus pauses at 12:30 remaining, then resumes from same point

**Severity:** breakage

**Setup:**

A focus session is running; elapsed is 12:30. No pause has occurred.

**Trigger:**

Marcus clicks PAUSE button. After 3 seconds, he clicks RESUME.

**Expected:**

Immediately after PAUSE: display freezes at 12:30, PAUSE button becomes RESUME. After clicking RESUME: countdown resumes from 12:30 (or within ±1 second). Session completion still fires at 25:00 total elapsed.

**Concern:**

Pause will not freeze the elapsed counter (it'll keep counting). Or resume will restart from 0 instead of resuming from pause point. Or the internal elapsed_ms will get reset.

**Property:**

If session is paused at elapsed E1, and resumed at wall-clock time T later, the elapsed counter must resume from E1, not from 0. Completion fires when total elapsed first exceeds session_duration.
