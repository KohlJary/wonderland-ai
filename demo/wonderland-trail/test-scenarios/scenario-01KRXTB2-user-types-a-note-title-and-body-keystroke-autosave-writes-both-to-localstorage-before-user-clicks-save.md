## Scenario 043: User types a note title and body; keystroke autosave writes both to localStorage before user clicks Save

**GUID:** 01KRXTB2N1T8SKB4XW9T1D9EW1
**Severity:** breakage

**Setup:**

EditorPane component is mounted. localStorage is empty. User has not yet interacted with the page.

**Trigger:**

User types 'My Experiment' in the title field, then tabs to the body field and types '# Results\n\nObserved precipitation.'

**Expected:**

After each keystroke, localStorage['noteDraft'] is updated with {title, body}. localStorage persists the partial content in real-time. No explicit Save click has occurred yet.

**Concern:**

If keystroke buffer is not implemented, the draft will be lost on page reload. This is the core feature — without it, the editor is not resilient to crash.

**Property:**

For all keystroke sequences in the editor's input fields, the most recent keystroke's result appears in localStorage['noteDraft'] within 100ms (or synchronously if no debounce).

**Implies:**
- Implies a question about debounce strategy — should every keystroke flush to localStorage, or only on pause? Story flags this as unclear. Recommend synchronous save on keystroke for v1 (simpler, safer).
