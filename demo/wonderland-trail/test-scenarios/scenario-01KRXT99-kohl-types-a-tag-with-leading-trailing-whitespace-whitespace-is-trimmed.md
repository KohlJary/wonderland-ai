## Scenario 015: Kohl types a tag with leading/trailing whitespace — whitespace is trimmed

**GUID:** 01KRXT99M7QSR234FW4T0095TW
**Severity:** degradation

**Setup:**

The editor is open. Kohl types '  experimental setup  ' (spaces before and after) in the tag input.

**Trigger:**

Kohl presses Enter or clicks Add.

**Expected:**

The tag is trimmed to 'experimental setup' (spaces removed). It appears as a chip with the trimmed text. No extra whitespace is visible in the chip label.

**Concern:**

If whitespace is not trimmed, two otherwise-identical tags ('experiment' vs ' experiment ') would be stored as different tags in the backend, causing accidental duplication and confusing the tag list.

**Property:**

Tag input is sanitized (trimmed) on entry
