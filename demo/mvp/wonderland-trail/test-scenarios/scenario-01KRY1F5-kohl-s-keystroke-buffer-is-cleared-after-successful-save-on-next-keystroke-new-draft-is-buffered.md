## Scenario 365: Kohl's keystroke buffer is cleared after successful Save; on next keystroke, new draft is buffered

**GUID:** 01KRY1F5JJWC63TXB9SQCCBZWM
**Severity:** degradation

**Setup:**

Kohl has saved a note successfully. The keystroke buffer in localStorage has been cleared. She continues editing — types 'new text' into the body.

**Trigger:**

Keystroke event fires in the editor's textarea (onChange handler).

**Expected:**

The editor state updates (body = 'new text'). The keystroke handler calls saveToLocalStorage(), which writes the updated state to localStorage. The buffer now contains the new draft {title, body: 'new text', ...}. If the page reloads before the next Save, the editor restores from localStorage and shows 'new text'.

**Concern:**

If the keystroke buffer is not re-initialized after a successful Save, subsequent keystrokes are not buffered. On page reload before the next Save, the user's new edits are lost.

**Property:**

keystroke buffer is refreshed after Save and captures new drafts
