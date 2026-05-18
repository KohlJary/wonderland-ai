## Scenario 320: Kohl opens the editor, types a few characters, and immediately closes the browser without clicking Save or reloading—on the next session, the buffer should restore her draft

**GUID:** 01KRY1CT0KYYZH13BXHBA5K1JN
**Severity:** silent-wrongness

**Setup:**

Kohl opens the editor in a fresh browser session. localStorage is empty. No prior saved notes exist.

**Trigger:**

Kohl types 'Preliminary findings:' into the title and closes the browser entirely (Force quit, power loss, or intentional closure).

**Expected:**

Before closing, the keystroke handler writes the buffer to localStorage after 300ms idle. On the next session (browser reopened), localStorage['noteBuffer'] exists and the editor restores {title: 'Preliminary findings:', body: ''} on mount. Kohl can continue editing without losing her start.

**Concern:**

If the keystroke buffer has a very short window to write before the browser closes (e.g., if the debounce timer hasn't fired yet), the data may be lost. The scenario tests the boundary: Kohl types, waits briefly, and closes. The buffer should capture this within the timeout window.

**Property:**

Keystroke buffer survives browser closure when 300ms has elapsed since the last keystroke.
