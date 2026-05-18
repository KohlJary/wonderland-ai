## Scenario 298: User closes tab immediately after typing; keystroke buffer is not yet flushed to localStorage

**GUID:** 01KRY1ARRE8QYC9GT63D0YD5GX
**Severity:** silent-wrongness

**Setup:**

Editor is open with empty title and body. keystroke buffer is not debounced — every keystroke writes synchronously to localStorage. Browser is about to close (user presses Ctrl+W or closes tab).

**Trigger:**

User types 't' into the title field. Immediately, before the onChange handler completes, the user closes the tab (the beforeunload or pagehide event fires).

**Expected:**

The typed 't' should appear in localStorage before the tab closes. When the editor is reopened, the title should show 't' (or the user should see their keystroke was saved).

**Concern:**

If localStorage.setItem() is asynchronous or buffered by the browser, and the tab closes before the write is flushed, the keystroke is lost silently. Kohl types 't', closes the tab, reopens it, and the editor is blank. She has no visual indication that her keystroke was lost — she'll assume the editor is broken or her typing didn't register.

**Property:**

For any single keystroke followed by immediate tab closure, the keystroke must be persisted to localStorage before the tab closes, or the user must receive a warning that the keystroke is unsaved.

**Implies:**
- Implies edge case: beforeunload / pagehide event ordering. Consider flushing to localStorage on unload events in addition to onChange.
