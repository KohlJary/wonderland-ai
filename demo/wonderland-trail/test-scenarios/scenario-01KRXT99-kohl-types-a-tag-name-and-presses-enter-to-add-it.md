## Scenario 010: Kohl types a tag name and presses Enter to add it

**GUID:** 01KRXT99M7QSR234FW4T0095TQ
**Severity:** breakage

**Setup:**

The editor is open with an empty note. The TagInput component is rendered below the title field. Kohl's cursor is in the tag text input.

**Trigger:**

Kohl types 'experimental-setup' and presses Enter.

**Expected:**

The tag 'experimental-setup' appears as a removable chip/badge below the input. The input field clears and is ready for the next tag. The tag persists in the component's tag list until Save is clicked.

**Concern:**

If Enter key doesn't register, or the chip doesn't appear, Kohl cannot add tags at all — the feature is broken. This is the core happy path.

**Property:**

Tag addition via keyboard is responsive and non-blocking
