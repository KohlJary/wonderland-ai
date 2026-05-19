## Scenario 292: User opens editor, closes without typing, page reloads—localStorage buffer is not created for an unchanged editor

**GUID:** 01KRY1AH3KPSQ1N168XD0XCQTV
**Severity:** delight

**Setup:**

Editor mounted, localStorage initially empty.

**Trigger:**

User does not type anything; browser is closed after 2 seconds.

**Expected:**

localStorage remains empty (or is explicitly cleared on mount if it was stale). On page reload, editor starts with empty state, not stale garbage.

**Concern:**

If every mount writes to localStorage even without keystroke, or if old buffers are not cleaned, users accumulate stale drafts. The spec says 'restore from localStorage if present, falling back to empty note', which implies: only write when user edits, only restore when there is something to restore.
