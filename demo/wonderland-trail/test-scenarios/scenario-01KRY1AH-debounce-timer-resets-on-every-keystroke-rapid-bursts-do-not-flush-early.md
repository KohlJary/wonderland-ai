## Scenario 293: Debounce timer resets on every keystroke; rapid bursts do not flush early

**GUID:** 01KRY1AH3KPSQ1N168XD0XCQTW
**Severity:** degradation

**Setup:**

Editor with empty state; a debounce timer is active (user just typed).

**Trigger:**

User types nothing for 200ms, then types 1 more character. The debounce timer should reset.

**Expected:**

The 300ms window resets from that final keystroke. localStorage does not flush at 200ms; it flushes at 500ms (200ms idle + 300ms from the last keystroke).

**Concern:**

Incorrect debounce implementation (e.g., 'write after 300ms of app lifetime' instead of 'write 300ms after the last keystroke') will either flush too early (defeating the debounce) or too late (holding state in memory longer than specified). The debounce must be 'trailing' (write after silence), not 'leading' or 'throttled'.
