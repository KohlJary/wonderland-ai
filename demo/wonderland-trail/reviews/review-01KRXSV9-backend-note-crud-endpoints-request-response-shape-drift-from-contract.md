## Review 007: Backend: Note CRUD endpoints — request/response shape drift from contract

**GUID:** 01KRXSV9CR7TF7TXQS670R3MHG
**Files reviewed:** src/backend/api/notes.py, src/backend/models.py
**Verdict:** request-changes

### Findings

#### change-required: Request field mismatch: tag_ids vs. tag_names
**Location:** src/backend/api/notes.py:35-42
**Quote:**

```
class NoteCreate(BaseModel):
    """
    Invariants enforced:
    - title: required, non-empty string (1-255 chars)
    - body: optional string, defaults to ""
    - tag_ids: optional array of tag name strings, defaults to []
```

**Read:** The NoteCreate class defines `tag_ids: list[str]` as the request field name for tag names.
**Concern:** Contract-note-01KRXRVT (Note Creation Envelope with Tags) specifies the request body should be {title, body, tag_names: [string]}, not tag_ids. The field name 'tag_ids' is misleading because these are names (strings), not IDs (integers). This will confuse the frontend and violate the established contract.
**Request:** Rename the field from `tag_ids` to `tag_names` in NoteCreate, NoteUpdate, and the _associate_tags function calls. Update the docstring to clarify these are tag names (strings), not IDs.

#### change-required: Response shape mismatch: tags array missing ID information
**Location:** src/backend/api/notes.py:77 and src/backend/models.py:50-51
**Quote:**

```
"tags": [tag.name for tag in self.tags]
```

**Read:** The to_dict() method returns tags as a simple list of strings (tag names only).
**Concern:** Contract-note-01KRXRVT specifies the response should include {tag_names: [string], tag_ids: [integer]} so the frontend can cache both for display and future updates. Without IDs in the response, the frontend cannot reference tags by ID (e.g., when sending PUT /notes/:id with updated tags). This breaks the atomic save contract.
**Request:** Change NoteResponse to include both tag names and IDs. Modify to_dict() to return tags as {tag_names: [string], tag_ids: [integer]} or change the TagResponse to be returned as {id: int, name: str} array. Verify the response shape matches contract-note-01KRXRVT exactly.

#### suggestion: Missing tag_ids or tag_objects in NoteResponse model definition
**Location:** src/backend/api/notes.py:68-80
**Quote:**

```
class NoteResponse(BaseModel):
    id: int
    title: str
    body: str
    tags: list[str]
    created_at: str
    updated_at: str
```

**Read:** The Pydantic NoteResponse model defines tags as list[str], but the response needs to include both IDs and names.
**Concern:** The model doesn't define what shape the tags array takes. If it should be list of TagResponse objects (which have id and name), the field type needs to reflect that. Right now the type annotation is list[str] but the contract specifies full tag objects.
**Request:** Either: (a) change the model to tags: list[TagResponse], or (b) add separate fields tag_names: list[str] and tag_ids: list[int] to match contract-note-01KRXRVT exactly, depending on which shape Tweedledee prefers. Include a comment citing the contract.

### Approvals

- The schema migration to normalize tags via a many-to-many relationship (note_tags table) is correct and necessary.
- The _associate_tags helper function correctly implements auto-create semantics: find-or-create tags by name, then associate with the note.
- Timezone handling in to_dict() is thoughtful: ensures all timestamps are UTC with Z suffix, handles both naive (SQLite) and aware datetimes.
- The CRUD endpoint implementation is well-structured: separate request/response models, proper error codes (404, 201), cascade deletes on remove_tag are correct.

### Cross-domain references

- The frontend will need to be updated to send/receive the corrected field names and response shape. Tweedledee will need clarification on whether tags should be list[TagResponse] or separate tag_names/tag_ids fields.
- The app entry point (src/backend/main.py) correctly includes the notes router, so that's good. But frontend/src/App.tsx still references the old Message API and doesn't render any editor component — this is a cross-ticket orphaning issue for Dodo to address (feature is only half-implemented).
