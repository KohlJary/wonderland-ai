## Scenario 144: User adds a 150-character tag; client-side validation should reject before sending to backend

**GUID:** 01KRXXWPY030EP5X13KFVQXC0R
**Severity:** silent-wrongness

**Setup:**

Editor is open. TagInput component is rendered. The input field has focus. No client-side tag length validation is currently implemented (code review shows no maxLength attribute, no length check in handleAddTag, per implementation-01KRXTP0).

**Trigger:**

User pastes a 150-character string (e.g., lorem ipsum text) into the tag input field and presses Enter.

**Expected:**

Per scenario-01KRXT9Z-user-attempts-to-add-a-tag-name-exceeding-100-characters: the tag is rejected client-side. Input field is NOT cleared. No chip is added. No error message is required yet (v1 scope), but silent rejection satisfies the acceptance criterion.

**Concern:**

Current TagInput.tsx does NOT validate tag length before calling onTagsChange. A 150-character tag will be added to the chips, appear to the user as a valid chip (visual confirmation bias), and then cause the entire POST /api/notes to fail with a 400 error when Save is clicked (per contract-note-01KRXRVT: 'each tag_name is 1-100 chars'). The user's note draft survives the error (Editor preserves state on failed save), but they see a generic error message 'Save failed: Error...' without understanding which field caused the failure. They must then debug by removing tags one-by-one to discover the culprit. This is silent-wrongness because the UI deceives the user into believing the tag is valid (by displaying it as a chip with no feedback) when it violates the backend contract.

**Property:**

For all tag names T with len(T) > 100, the component must reject T BEFORE calling onTagsChange. The input field must NOT be cleared, allowing the user to edit and re-submit. Invariant: no tag with len(T) > 100 shall ever be added to the chip list.

**Implies:**
- Implies contract alignment: TagInput.tsx must enforce the 1-100 character constraint per contract-note-01KRXRVT before accepting a tag. Flag for Tweedledee for implementation fix.
- Implies test: Tweedledee should write a unit test (vitest) for TagInput that verifies long tags are rejected.
