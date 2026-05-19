## Implementation 007: Fix response shape: tags with names and IDs

**GUID:** 01KRXSZV831SFDYHJ15GRVM9VV
**Side:** backend
**Ticket:** response-shape-mismatch-tags-array-missing-id-information
**Contract:** contract-note-004/v1 (Note Creation Envelope with Tags). Request: POST /notes {title, body?, tag_names?}. Response: {id, title, body, tag_names: [string], tag_ids: [integer], created_at, updated_at} per contract-note-01KRXRVT.
**Ready for review:** yes

**Approach:**

Updated NoteResponse Pydantic model to replace single 'tags' field with 'tag_names: list[str]' and 'tag_ids: list[int]'. Updated Note.to_dict() to return both arrays. Updated all CRUD endpoints' contracts and docstrings. All endpoints (POST /api/notes, GET /api/notes, GET /api/notes/{id}, PUT /api/notes/{id}, POST /api/notes/{id}/tags) now return the complete response shape with tag names and IDs.

**Invariants Enforced:**
- tag_names array is returned in response: list of strings matching the names of associated tags
- tag_ids array is returned in response: list of integers matching the IDs of associated tags
- Both arrays are always synchronized: same length, same ordering (tags sorted by their internal order in the SQLAlchemy relationship)
- Empty tags on a note produce empty tag_names and tag_ids arrays (never null)

**Schema Changes:**

No schema changes. Existing notes table, tags table, and note_tags junction table structure unchanged. Only the response serialization (to_dict()) was updated to include both names and IDs.

**Failure Modes Handled:**
- Empty tag list: returns tag_names=[], tag_ids=[] (not null)
- Tag creation failure: if tag auto-create fails (e.g., name too long), endpoint returns 422 validation error before write
- Tag deletion: when a tag is removed from a note, both tag_names and tag_ids are updated atomically in the response

**Files:**
- src/backend/models.py: Updated Note.to_dict() to return tag_names and tag_ids arrays instead of simple tags array
- src/backend/api/notes.py: Updated NoteResponse model (tag_names, tag_ids fields), NoteCreate/NoteUpdate models (tag_names field naming), and all endpoint docstrings to reflect new contract shape

**Open Questions for Pair:**
- Confirmed: response shape now matches contract-note-004 exactly (tag_names and tag_ids both present). Frontend can now cache full tag objects for future updates and autocomplete.

**Known Limitations:**
- No pagination on GET /api/notes yet; pagination deferred to search-endpoint work
- No audit logging yet (Queen ruling-003); endpoints don't write to audit_log table
- No multi-tab collision detection (Queen ruling-004 If-Match header); PUT /notes/{id} has no version check
