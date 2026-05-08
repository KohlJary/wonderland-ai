## Scenario 005: Browser tab loses focus mid-timer; Marcus switches back and timer has advanced

**Severity:** silent-wrongness

**Setup:**

A focus session is running with 10:00 remaining. Marcus's tab has focus.

**Trigger:**

Marcus switches to another browser tab (app loses focus). Waits 5 seconds. Switches back to timer tab.

**Expected:**

Timer has correctly advanced while tab was unfocused. Display shows ~9:55 (not still showing 10:00). Session completion still fires at correct absolute time.

**Concern:**

When tab loses focus, the JavaScript tick loop may pause or the timer may rely on RAF which stops in hidden tabs. When tab regains focus, elapsed time will not have advanced, creating a gap. User sees display jump backward, or completion fires late.

**Property:**

session.elapsed_ms must be tracked independently of UI update rate. Completion time is absolute wall-clock, not relative to last UI render. Resuming from tab-hidden state must sync elapsed_ms to current time.
