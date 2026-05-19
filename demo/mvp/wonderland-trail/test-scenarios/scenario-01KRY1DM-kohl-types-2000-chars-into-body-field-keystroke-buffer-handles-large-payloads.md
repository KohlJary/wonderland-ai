## Scenario 341: Kohl types 2000 chars into body field—keystroke buffer handles large payloads

**GUID:** 01KRY1DM2GCZ9MKM8TTD72W1P6
**Severity:** degradation

**Setup:**

Kohl opens the editor. She pastes a 2000-character block of text (a research note) into the body field.

**Trigger:**

The final keystroke (paste completes) triggers the keystroke-buffer write to localStorage. The Editor component serializes {title, body, tags} to JSON and calls localStorage.setItem('editor_draft', JSON).

**Expected:**

The setItem completes within 50ms (modern browsers can serialize and write 2KB to localStorage in <10ms). The keystroke handler does not block; the editor remains responsive. The user sees the text appear in the textarea without lag.

**Concern:**

If JSON serialization of a 2000-char body takes >100ms (rare but possible on very old devices or if the object is deeply nested), the keystroke handler blocks the thread. Subsequent keystrokes queue up and the editor feels sluggish. This is a degradation, not breakage: the buffer still works, but the UX is poor.

**Property:**

keystroke-buffer-performance-on-large-body

**Implies:**
- serialize-and-write-to-localstorage-is-fast
- editor-remains-responsive-during-buffer-write
