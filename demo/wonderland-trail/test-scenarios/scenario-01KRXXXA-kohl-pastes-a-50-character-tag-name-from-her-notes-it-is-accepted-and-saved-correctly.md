## Scenario 153: Kohl pastes a 50-character tag name from her notes; it is accepted and saved correctly

**GUID:** 01KRXXXAWK63FBTGKJSS5NBRY5
**Severity:** degradation

**Setup:**

Kohl has a multi-word tag in her notes: 'distributed-consensus-protocols'. She copies this text and pastes it into the tag input field.

**Trigger:**

Kohl pastes the text, presses Enter to add the tag.

**Expected:**

The tag 'distributed-consensus-protocols' appears as a chip. She clicks Save and the tag is sent to the backend and persists. No error message appears.

**Concern:**

If the tag input field rejects long tag names with no warning, or if the save fails with a validation error that is not surfaced to Kohl, she will be confused about why her tag disappeared or why the save failed. The user experience is degraded.

**Property:**

Tag input accepts tag names up to the backend constraint (max 100 chars) and surfaces validation errors clearly if the limit is exceeded.

**Implies:**
- Client-side validation should allow tags up to 100 characters (matching the backend constraint).
- If Kohl pastes a tag that exceeds 100 chars, the input should reject it (or warn her) before she adds it as a chip.
- The save endpoint error response should include which tag caused the validation failure, so Kohl knows which chip to remove or edit.
