## Ticket 018: Response shape mismatch: tags array missing ID information

**GUID:** 01KRXSV9D2E5ENX2ZHZJPSV84C
**Sources:** kohl-can-create-and-save-experimental-notes-with-title-and-body, backend-note-crud-endpoints-request-response-shape-drift-from-contract
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``backend-note-crud-endpoints-request-response-shape-drift-from-contract`` (change-required):

**Concern:** Contract-note-01KRXRVT specifies the response should include {tag_names: [string], tag_ids: [integer]} so the frontend can cache both for display and future updates. Without IDs in the response, the frontend cannot reference tags by ID (e.g., when sending PUT /notes/:id with updated tags). This breaks the atomic save contract.

**Request:** Change NoteResponse to include both tag names and IDs. Modify to_dict() to return tags as {tag_names: [string], tag_ids: [integer]} or change the TagResponse to be returned as {id: int, name: str} array. Verify the response shape matches contract-note-01KRXRVT exactly.

**Location:** ``src/backend/api/notes.py:77 and src/backend/models.py:50-51``

**Acceptance:**
- Change NoteResponse to include both tag names and IDs. Modify to_dict() to return tags as {tag_names: [string], tag_ids: [integer]} or change the TagResponse to be returned as {id: int, name: str} array. Verify the response shape matches contract-note-01KRXRVT exactly.
