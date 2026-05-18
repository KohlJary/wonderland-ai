## Scenario 059: Deleting a tag association with a non-existent tag_id returns 404

**GUID:** 01KRXTD96CAEAJCAJEH0RQWM03
**Severity:** degradation

**Setup:**

User constructs a DELETE /api/notes/{id}/tags/99999 with a tag_id=99999 that doesn't exist in the database.

**Trigger:**

DELETE request with invalid tag_id.

**Expected:**

Returns 404 (Tag not found). The note is not modified.

**Concern:**

The code queries for the tag; if not found, raises HTTPException(404). Correct behavior. But there are two cases: (1) tag_id doesn't exist, (2) tag exists but is not associated with this note. Both return 404, but the error message should distinguish them.

**Property:**

For all DELETE requests with a non-existent tag_id, the response is 404.

**Implies:**
- Implies tests: test_delete_tag_association_with_invalid_tag_id, test_delete_tag_association_with_unassociated_tag.
