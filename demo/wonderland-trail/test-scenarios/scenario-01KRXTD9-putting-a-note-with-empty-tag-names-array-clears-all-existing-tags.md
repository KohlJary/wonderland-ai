## Scenario 056: Putting a note with empty tag_names array clears all existing tags

**GUID:** 01KRXTD96BAEAJCAJEH0RQWM00
**Severity:** degradation

**Setup:**

POST /api/notes creates a note with tag_names=['research', 'experiment']. Then PUT /api/notes/{id} with {tag_names: []}.

**Trigger:**

PUT request with tag_names explicitly set to empty array.

**Expected:**

Since tag_names is optional in NoteUpdate, the semantics should be: omitting tag_names means no change; sending tag_names=[] means clear all tags OR should be rejected as invalid.

**Concern:**

The code checks 'if payload.tag_names is not None' and empty list is not None, so tags are cleared. This is probably not user intent — they likely omitted the field, not sent an empty array. The endpoint silently does something unexpected. This is silent wrongness in the contract-level semantics.

**Property:**

For all notes N, if tag_names=[] is sent in PUT, all tags are removed. If tag_names is omitted, tags are unchanged.

**Implies:**
- Implies contract clarification: Tweedles and Cat must agree if tag_names=[] should clear tags or be invalid. The contract-notes don't specify this.
- Implies tests: test_put_note_with_empty_tag_names_clears_tags documents current behavior; test_put_note_without_tag_names_preserves_tags verifies omission.
