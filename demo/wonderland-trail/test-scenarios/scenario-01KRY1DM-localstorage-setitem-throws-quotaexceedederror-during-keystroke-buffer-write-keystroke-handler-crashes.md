## Scenario 344: localStorage.setItem throws QuotaExceededError during keystroke buffer write—keystroke handler crashes

**GUID:** 01KRY1DM2GCZ9MKM8TTD72W1P9
**Severity:** breakage

**Setup:**

Kohl has already filled localStorage with 4MB of other data (app state, cached images, etc.). She opens the editor and starts typing. The keystroke buffer is configured to write the full {title, body, tags} on each keystroke (no debounce for this test scenario).

**Trigger:**

Kohl types a character. The keystroke handler calls localStorage.setItem('editor_draft', JSON.stringify({...})), which throws QuotaExceededError because localStorage quota is exceeded.

**Expected:**

The keystroke handler catches the error, logs it, and continues. The keystroke is registered in the editor component's state (the user sees the character appear in the textarea), but it is not written to localStorage. On next keystroke, the handler attempts to write again (same error) or gracefully degrades to not persisting. Kohl is not blocked; she can keep typing.

**Concern:**

If the keystroke handler does not catch the error, the exception propagates and crashes the component. The keystroke is not registered. Kohl types and nothing appears—a breakage. Even worse, the editor component may unmount and Kohl's work is lost. This is a high-severity silent-wrongness scenario: the user believes the keystroke was registered (because they typed) but it was actually dropped.

**Property:**

keystroke-buffer-quota-exceeded-handling

**Implies:**
- localstorage-setitem-errors-are-caught
- keystroke-is-still-registered-even-if-buffer-write-fails
- editor-does-not-crash-on-quota-exceeded
