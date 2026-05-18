## Scenario 046: User types rapidly (20+ keystrokes per second); no keystrokes are dropped and all content is saved

**GUID:** 01KRXTB2N1T8SKB4XW9T1D9EW4
**Severity:** silent-wrongness

**Setup:**

EditorPane is mounted with an empty draft. User pastes or rapid-types a long block of text into the body field.

**Trigger:**

Clipboard paste of 500 characters into the body field, or simulated rapid keystroke sequence (20+ keystrokes in <1 second).

**Expected:**

All characters appear in the field and are saved to localStorage['noteDraft']. No characters are lost.

**Concern:**

If the keystroke buffer uses event debouncing with a delay (e.g., 500ms), rapid typing may not be captured in time. React's synthetic event pooling or slow localStorage.setItem calls might cause characters to be dropped or interleaved.

**Property:**

For all keystroke sequences, including rapid pastes, localStorage['noteDraft'] contains all characters that appear in the input fields.

**Implies:**
- Implies a decision about debounce delay. Synchronous (0ms debounce) is safest; debounced saves risk data loss under rapid input.
