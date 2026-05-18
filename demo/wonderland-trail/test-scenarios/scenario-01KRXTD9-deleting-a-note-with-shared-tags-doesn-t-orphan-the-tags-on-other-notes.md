## Scenario 058: Deleting a note with shared tags doesn't orphan the tags on other notes

**GUID:** 01KRXTD96CAEAJCAJEH0RQWM02
**Severity:** curiosity

**Setup:**

Two notes share a tag 'shared'. DELETE /api/notes/{id1} deletes the first note.

**Trigger:**

DELETE request on a note whose tags are also associated with other notes.

**Expected:**

The first note is deleted. Its association to the tag is deleted (CASCADE on note_tags). The tag row persists in the database (tags are not cascade-deleted). The second note's tags remain intact.

**Concern:**

The cascade is on the *association*, not the tag itself. Worth verifying that SQLAlchemy doesn't accidentally delete the tag when only the association should be deleted.

**Property:**

For all tags T shared by notes N1 and N2, if N1 is deleted, T still exists in the database and is still associated with N2.

**Implies:**
- Implies test: test_delete_note_with_shared_tags_doesnt_orphan_tag.
