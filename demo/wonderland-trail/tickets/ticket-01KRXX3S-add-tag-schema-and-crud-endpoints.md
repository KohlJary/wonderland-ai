## Ticket 032: Add tag schema and CRUD endpoints

**GUID:** 01KRXX3SA1BRDRD799772ZAZC1
**Sources:** kohl-organizes-notes-with-optional-tags
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-2 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: add-tag-inputs-to-editor-ui, display-tags-in-note-list
- Blocked by: create-and-save-notes-with-markdown-bodies
- Soft: —

**Description:**

Create the database schema for tags (id, name, created_at) and tag associations (note_id, tag_id). Implement endpoints: POST /tags (create), GET /tags (list), POST /notes/{id}/tags (add tag to note), DELETE /notes/{id}/tags/{tag_id} (remove). Return tag lists with note queries.

**Acceptance:**
- Tags table exists with id, name, created_at columns
- note_tags association table exists
- POST /tags creates a tag and returns id + name
- GET /tags returns all tags
- POST /notes/{id}/tags associates an existing tag to a note
- DELETE /notes/{id}/tags/{tag_id} removes association
- GET /notes/{id} includes tags array in response

**Risk:**

If tag association needs to handle duplicate prevention or tag-name uniqueness constraints, expand to 2-3 days.
