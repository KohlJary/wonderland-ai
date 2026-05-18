## Scenario 340: Kohl types 50 chars, closes tab within 2 seconds—keystroke buffer persists on reload

**GUID:** 01KRY1DM2GCZ9MKM8TTD72W1P5
**Severity:** silent-wrongness

**Setup:**

Kohl opens the editor (fresh page, no localStorage). Editor is empty: title='', body=''. Keystroke buffer debounce is 500ms.

**Trigger:**

Kohl types 'Important note about the experiment' (36 chars) into the body textarea in ~1 second total. On the 36th keystroke, Kohl immediately closes the tab (before the 500ms debounce fires and writes to localStorage).

**Expected:**

On page reload, localStorage contains the incomplete buffer. Editor restores the buffer and shows 'Important note about the exper' in the body field. Kohl sees her partial keystroke sequence and can decide to continue or clear.

**Concern:**

If the keystroke buffer debounce is not working correctly (e.g., debounce timer is lost on tab close), the partial keystroke will not be written to localStorage. Kohl reloads and sees a blank editor, believing her typing was lost. Silent-wrongness: the system appears to work (no error) but discards her input.

**Property:**

keystroke-buffer-survives-rapid-close

**Implies:**
- debounce-timer-fires-on-unmount
- unwritten-buffer-is-flushed-before-page-unload
