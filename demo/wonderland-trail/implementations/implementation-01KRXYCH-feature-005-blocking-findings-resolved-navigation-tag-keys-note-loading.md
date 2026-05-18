## Implementation 033: Feature 005 blocking findings resolved: navigation, tag keys, note loading

**GUID:** 01KRXYCH7H0T9Y3G7KZB1GX4NT
**Side:** frontend
**Ticket:** feature-005-kohl-organizes-notes-with-optional-tags
**Contract:** contract-note-001 (Note model CRUD), contract-note-014 (tag_names and tag_ids in responses), Editor-Editor Layout contract (noteId prop threading)
**Ready for review:** no

**Approach:**

App.tsx now manages selectedNoteId state and threads it through handleEditNote → EditorLayout.noteId → Editor. Editor correctly fetches the note by ID on mount (readNote), or restores from localStorage if creating a new note. NoteList uses stable tag_ids for React keys. Clicking a note in NoteList now correctly opens it in the editor with all fields populated.

**UI States Implemented:**
- list: NoteList displays all notes with tags as badges, clickable
- editor-loading: spinner while fetching note by ID
- editor-new: editor opens in create mode with empty fields and localStorage restore
- editor-edit: editor opens with note fields populated from backend

**Client State:**

selectedNoteId tracked in App.tsx; Editor state (title, body, tags) stored locally in component state and mirrored to localStorage on keystroke; lastSavedId tracks the most recently saved note's ID for success message display

**Files:**
- frontend/src/App.tsx: added selectedNoteId state, handleEditNote callback, NoteList import
- frontend/src/EditorLayout.tsx: added noteId and onSave props, passed to Editor
- frontend/src/Editor.tsx: added noteId prop, useEffect to load existing note, updateNote call for editing, loadingNote spinner
- frontend/src/NoteList.tsx: new file, all tag rendering and note-click navigation

**Open Questions for Pair:**
- Tag normalization: should whitespace-only names ('  ') be stripped or rejected? Should leading/trailing whitespace be normalized?
- Case sensitivity: should tags be case-insensitive (research = Research)? Current implementation treats them as case-sensitive.
- Scope clarification: is inline tag editing in NoteList (add/remove tags without opening editor) part of v1 Feature 005, or fast-follow?

**Known Limitations:**
- Tag editing only available via Editor, not inline in NoteList (per current product scope, pending clarification)
- No multi-tab collision detection yet (versioning contract not yet implemented)
- No offline queuing (v1 requires backend availability for Save)
