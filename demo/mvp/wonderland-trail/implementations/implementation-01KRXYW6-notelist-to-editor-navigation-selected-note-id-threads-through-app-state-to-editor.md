## Implementation 042: NoteList-to-Editor navigation: selected note ID threads through App state to Editor

**GUID:** 01KRXYW6ZHNJQGTKPQ4C96GPEC
**Side:** frontend
**Ticket:** notelist-to-editor-navigation-is-broken-selected-note-id-never-reaches-editorlayout
**Contract:** Thread contract: App.tsx → EditorLayout (noteId: number | null). EditorLayout → Editor (noteId: number | null). Editor → API: readNote(id) returns Promise<Note> with fields {id, title, body, tag_names, tag_ids, created_at, updated_at}. Per contract-note-01KRXRTT (Note CRUD) and contract-note-01KRXXDG (GET /api/notes/{id} response shape).
**Ready for review:** yes

**Approach:**

App.tsx maintains selectedNoteId state (useState<number | null>). When user clicks a note in NoteList, handleEditNote(noteId) callback sets selectedNoteId and navigates to editor view via setView('editor'). EditorLayout receives noteId prop and passes to Editor. Editor.useEffect calls readNote(noteId) on mount if noteId is provided, fetching the note and hydrating title/body/tags fields. On save, handleEditorSave clears selectedNoteId and returns to list view.

**UI States Implemented:**
- editor-loading: spinner shown while fetching note from backend on mount (loadingNote state)
- editor-edit: existing note loaded and displayed, user can edit title/body/tags
- editor-new: no noteId provided, editor starts blank or restores from localStorage
- editor-error: save failed, error message shown, state preserved
- editor-success: save succeeded, temporary success message shown
- notelist-loading: spinner while fetching notes on mount
- notelist-display: notes rendered with title/preview/tags/date, click handler routes to editor

**Client State:**

App.tsx: selectedNoteId (number | null, cleared after save). Editor.tsx: state = {title, body, tags}, written to localStorage on every keystroke, cleared after successful save. EditorLayout.tsx: previewBody string (driven by Editor's onBodyChange callback). NoteList.tsx: notes array from fetch, not persisted. localStorage keystroke buffer survives page reload, cleared on save.

**Files:**
- frontend/src/App.tsx: selectedNoteId state (line 34), handleEditNote callback (line 63), EditorLayout.noteId prop (line 102)
- frontend/src/EditorLayout.tsx: EditorLayoutProps.noteId?: number | null (line 15), passes to Editor (line 22)
- frontend/src/Editor.tsx: noteId prop (line 28), useEffect loads note (line 54-70), handles create vs. update (line 130-145)
- frontend/src/NoteList.tsx: handleNoteClick calls onEdit(noteId) (line 58)

**Known Limitations:**
- Tag inline editing in NoteList is not implemented (read-only display). Tags can only be edited by opening the note in EditorLayout.
- Multi-tab collision detection deferred to v1.1; version_id field from backend is not cached or compared for staleness.
