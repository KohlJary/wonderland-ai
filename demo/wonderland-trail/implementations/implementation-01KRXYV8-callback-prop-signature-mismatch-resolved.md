## Implementation 040: Callback prop signature mismatch resolved

**GUID:** 01KRXYV8NT9NMEHFEK016981Y7
**Side:** frontend
**Ticket:** feature-005-kohl-organizes-notes-with-optional-tags
**Contract:** contract-note-01KRXXDG (GET /api/notes response includes tag_names and tag_ids), NoteListProps.onEdit type contract: (noteId: number) => void
**Ready for review:** yes

**Approach:**

NoteList.onEdit prop signature (noteId: number) => void is now matched by App.tsx's handleEditNote callback, which accepts the noteId argument and uses it to set selectedNoteId state. EditorLayout receives noteId prop and passes it to Editor, which loads the note from backend on mount via readNote(noteId). The contract is satisfied: when user clicks a note in NoteList, the noteId flows through the callback chain into EditorLayout and Editor, enabling the edit workflow.

**UI States Implemented:**
- edit-existing-note: Editor loads note from backend when noteId is provided
- new-note: Editor starts empty when noteId is null/undefined
- loading-note: Editor shows 'Loading note…' spinner while fetching from backend

**Client State:**

App.tsx maintains selectedNoteId state (number | null). When user clicks a note in NoteList, onEdit callback receives the noteId and App sets selectedNoteId, triggering view switch to editor with noteId threaded down to EditorLayout. EditorLayout passes noteId to Editor, which fetches the note from the server and populates local editor state (title, body, tags). localStorage buffer persists keystroke state independently of noteId flow.

**Files:**
- frontend/src/App.tsx: handleEditNote callback accepts and uses noteId parameter
- frontend/src/NoteList.tsx: onEdit called with noteId argument per handleNoteClick
- frontend/src/EditorLayout.tsx: accepts noteId prop, passes to Editor
- frontend/src/Editor.tsx: accepts noteId prop, loads note on mount via readNote()
