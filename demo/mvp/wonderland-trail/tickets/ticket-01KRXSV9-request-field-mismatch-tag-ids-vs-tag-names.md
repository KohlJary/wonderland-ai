## Ticket 017: Request field mismatch: tag_ids vs. tag_names

**GUID:** 01KRXSV9D0TTVZ60AE3G5SEC2V
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

**Concern:** Contract-note-01KRXRVT (Note Creation Envelope with Tags) specifies the request body should be {title, body, tag_names: [string]}, not tag_ids. The field name 'tag_ids' is misleading because these are names (strings), not IDs (integers). This will confuse the frontend and violate the established contract.

**Request:** Rename the field from `tag_ids` to `tag_names` in NoteCreate, NoteUpdate, and the _associate_tags function calls. Update the docstring to clarify these are tag names (strings), not IDs.

**Location:** ``src/backend/api/notes.py:35-42``

**Acceptance:**
- Rename the field from `tag_ids` to `tag_names` in NoteCreate, NoteUpdate, and the _associate_tags function calls. Update the docstring to clarify these are tag names (strings), not IDs.
