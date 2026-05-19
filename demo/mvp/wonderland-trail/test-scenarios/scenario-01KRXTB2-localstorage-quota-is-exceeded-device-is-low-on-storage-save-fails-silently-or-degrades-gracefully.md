## Scenario 049: localStorage quota is exceeded (device is low on storage); save fails silently or degrades gracefully

**GUID:** 01KRXTB2N1T8SKB4XW9T1D9EW7
**Severity:** curiosity

**Setup:**

Device's localStorage quota is nearly full (e.g., 4.9/5 MB used on a typical browser). User types a large note.

**Trigger:**

User types 500+ kilobytes of content into the body field, exceeding quota.

**Expected:**

Either: (a) localStorage.setItem throws a QuotaExceededError, which is caught and logged (not shown to user as a crash), or (b) the keystroke buffer degrades to not save beyond quota (user is warned), or (c) older entries are cleaned up.

**Concern:**

Uncaught QuotaExceededError will crash the keystroke handler and the user's input may not be accepted.

**Property:**

For all input sizes, the keystroke handler does not crash the component if localStorage throws an exception.

**Implies:**
- Implies error handling strategy: wrap localStorage.setItem in try-catch and log quota errors, don't throw to the user.
