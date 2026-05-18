## Scenario 288: User rapidly types 100 characters—localStorage is written at most every 300ms, not on every keystroke

**GUID:** 01KRY1AH3KPSQ1N168XD0XCQTQ
**Severity:** degradation

**Setup:**

Editor mounted with empty state. localStorage.setItem is a spy to track call count.

**Trigger:**

User types 100 characters rapidly (e.g., 10 chars per 50ms, simulating 200 chars/second).

**Expected:**

localStorage.setItem is called roughly 1–2 times (once immediately on first keystroke, once at debounce boundary), not 100 times.

**Concern:**

Current implementation calls localStorage.setItem on every onChange event, which fires on every keystroke. On a fast typist or rapid paste, this hits localStorage 50–100+ times for the same logical edit, causing performance degradation on devices with slow storage I/O (older phones, slower SSDs). The ticket specifies 300ms debounce; spec is not met.
