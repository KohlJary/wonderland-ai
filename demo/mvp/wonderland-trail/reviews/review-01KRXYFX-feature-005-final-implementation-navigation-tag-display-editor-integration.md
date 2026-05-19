## Review 034: Feature 005 final implementation — navigation, tag display, editor integration

**GUID:** 01KRXYFXF3ZNDN8XTPFEMXG07H
**Files reviewed:** src/frontend/App.tsx, src/frontend/EditorLayout.tsx, src/frontend/Editor.tsx, src/frontend/NoteList.tsx, src/backend/api/notes.py, src/backend/models.py
**Verdict:** accept

### Approvals

- Navigation contract is now coherent: selectedNoteId threads from NoteList.onEdit() → App state → EditorLayout prop → Editor.noteId, with Editor correctly loading existing notes via readNote() on mount and creating new notes when noteId is absent. The flow is clear and testable.
- React key anti-pattern fixed: NoteList renders tags with key={`tag-${tagId}`} (using stable tag_ids from backend) instead of array indices. This prevents unnecessary DOM remounting on tag list mutations.
- Editor correctly differentiates create (POST) vs. edit (PUT) flows: when noteId is provided, Editor loads the existing note; when null, Editor initializes a blank form. handleSave() calls createNote() or updateNote() accordingly. The dual flow is well-separated and readable.
- Cross-ticket coherence verified: backend contract-note-014 specifies GET /api/notes response includes {id, title, body, tag_names: string[], tag_ids: number[], created_at, updated_at}. Frontend correctly consumes all fields. Tag rendering iteration maintains index correspondence between tag_names[i] and tag_ids[i] per the backend's to_dict() semantics.
- Tag input in Editor is wired to state correctly: onTagAdd() and onTagRemove() manage the local tag list, which is sent to backend via POST/PUT request body as {tag_names: string[]}. Response includes both tag_names and tag_ids for display and caching.
- Error handling is preserved: Editor shows error messages on API failures, keeps Save button disabled during isSaving state, and preserves localStorage on any failure. localStorage is only cleared on 200 response.
- NoteList displays notes in reverse chronological order (as returned by backend), renders tag badges inline with proper styling, and the click-to-edit flow correctly invokes onEdit(noteId). Empty-tags case is handled (conditional rendering prevents empty badge rows).

### Cross-domain references

- Queen's ruling-004 on multi-tab collision detection: the Editor caches revision_id from POST/PUT responses and compares it on next load; If-Match header support for collision detection is ready for M3 contract negotiation between Tweedles. Not required for v1 shipping, but the groundwork is in place.
- Search feature (Feature 003) depends on this: the search endpoint (contract-note-008) consumes the same Note response shape (id, title, body_preview, tag_names, tag_ids, created_at). Coherence verified.
- Mad Hatter's test scenarios on tag edge cases (whitespace normalization, case sensitivity, concurrent creation, shared tag preservation): these are documented in test_tag_scenarios.py and ready for tea-party when tickets are cut for whitespace handling and case-sensitivity rules.
