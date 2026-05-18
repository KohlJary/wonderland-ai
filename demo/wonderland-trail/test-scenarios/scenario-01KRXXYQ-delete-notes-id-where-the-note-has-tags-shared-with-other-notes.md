## Scenario 166: DELETE /notes/{id} where the note has tags shared with other notes

**GUID:** 01KRXXYQD08R1GFPSWEN11326Z
**Severity:** curiosity

**Setup:**

Note A and Note B both have tag 'shared'. Note C has tag 'other'. Delete Note A.

**Trigger:**

DELETE /api/notes/{note_a_id}.

**Expected:**

Note A is deleted. Tag 'shared' still exists. Note B still has the 'shared' tag. Tag 'other' is unaffected.

**Concern:**

The note_tags association has ondelete='CASCADE' on note_id, so the association row is deleted. The Tag model has no cascade, so the tag persists. This is correct per schema design (tags can be shared, so shouldn't be deleted with the note).

**Property:**

Deleting a note never cascade-deletes tags; tags persist and may be reused by other notes.
