## Scenario 060: Associating a tag that is already on the note is idempotent

**GUID:** 01KRXTD96CAEAJCAJEH0RQWM04
**Severity:** curiosity

**Setup:**

POST /api/notes creates a note with tag_names=['research']. Then POST /api/notes/{id}/tags with tag_name='research' again.

**Trigger:**

POST request to associate an already-associated tag.

**Expected:**

The endpoint is a no-op. The tag appears once in the response, not duplicated.

**Concern:**

The code checks 'if tag not in note.tags' before appending. This is correct and idempotent behavior. Worth confirming the response contains only one copy of the tag.

**Property:**

For all notes N and tags T, POST /api/notes/{id}/tags with tag_name=T is idempotent: repeating the request does not change the result.

**Implies:**
- Implies test: test_associate_tag_is_idempotent.
