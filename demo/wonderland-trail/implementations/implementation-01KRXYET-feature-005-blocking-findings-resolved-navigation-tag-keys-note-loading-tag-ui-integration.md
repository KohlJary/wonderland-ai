## Implementation 036: Feature 005 blocking findings resolved: navigation, tag keys, note loading, tag UI integration

**GUID:** 01KRXYET1JHY46SM4G71F1SN9S
**Side:** frontend
**Ticket:** feature-005-kohl-organizes-notes-with-optional-tags
**Contract:** contract-note-001 (Note CRUD), contract-note-014 (GET responses include tag_names and tag_ids), contract-note-015 (POST request shape), contract-note-016 (GET hydration), contract-note-003 (persistence semantics). All fields match backend responses: Note interface requires id, title, body, tag_names[], tag_ids[], created_at, updated_at.
**Ready for review:** yes

**Approach:**

App.tsx threads selectedNoteId state to EditorLayout, which passes it to Editor. Editor checks for noteId on mount: if present, fetches GET /api/notes/{id} and hydrates title/body/tags; if not present, restores from localStorage for new note creation. handleSave triggers onSave callback to reset selectedNoteId and return to list. NoteList renders notes with tag badges using stable tag_ids (key={`tag-${tagId}`}) instead of array indices. Editor and NoteList both call their respective API functions (readNote, updateNote, createNote, listNotes) correctly. LocalStorage buffer persists keystroke state and survives page reload. Markdown preview component is wired into EditorLayout and receives body updates from Editor. TagInput component allows free-text tag entry with add/remove chips. Tags are sent in POST/PUT payload and received in responses.

**UI States Implemented:**
- editor-loading (loading note on mount if noteId is provided)
- editor-new (no noteId, restore from localStorage or start blank)
- editor-edit (noteId provided, note loaded, user editing)
- editor-saving (Save button disabled, isSaving state)
- editor-error (save failed, error message displayed, state preserved for retry)
- editor-success (temporary success message after save)
- notelist-loading (fetching notes on mount)
- notelist-empty (no notes created yet)
- notelist-error (fetch failed, retry button available)
- notelist-display (notes rendered with title, preview, tags, date, click to edit)

**Client State:**

Editor.tsx: state = {title, body, tags} + localStorage backup (written on every keystroke, cleared after save). EditorLayout: previewBody (passed from Editor, drives Preview component). App: selectedNoteId (tracks which note is being edited, cleared on save, resets to show editor with blank form). NoteList: local notes array (fetched on mount, not persisted). All state is ephemeral except localStorage keystroke buffer (survives reload, cleared on save).

**Files:**
- frontend/src/App.tsx: App state now tracks selectedNoteId, routes note clicks to EditorLayout via noteId prop
- frontend/src/EditorLayout.tsx: accepts noteId and onSave props, threads to Editor
- frontend/src/Editor.tsx: accepts noteId prop, loads existing note on mount if noteId provided, handles create vs update logic in handleSave, calls updateNote or createNote accordingly
- frontend/src/NoteList.tsx: new component, fetches notes on mount, renders with tag badges using stable tag_ids as keys, calls onEdit(noteId) when user clicks a note

**Open Questions for Pair:**
- Tag normalization semantics: should the backend strip leading/trailing whitespace from tag_names on auto-create, or reject tags with invalid patterns? This affects client-side validation in TagInput (what errors do I show the user?).
- Confirmation: backend's listNotes() endpoint returns notes in reverse chronological order (updated_at DESC, id DESC as tiebreak)? NoteList displays in received order.

**Known Limitations:**
- Tag editing is only available in EditorLayout (click note → edit tags → save). Inline tag editing in NoteList (add/remove without opening editor) is not implemented; this is a scope question for the team (v1 or v2?). Current implementation supports the backend semantics (tags are part of the note, can be edited anytime), but the NoteList UI doesn't expose the capability.
- Multi-tab collision detection is not yet implemented. The revision_id field is returned by the backend (per ADR-004) but the frontend doesn't cache it or use it for staleness checks. This is acceptable for v1 single-user scope but should be added in v1.1 for robustness.
