## Implementation 034: NoteList component with tag display and click-to-edit navigation

**GUID:** 01KRXYCN9BVWWYW5E0362D4S40
**Side:** frontend
**Ticket:** feature-005-kohl-organizes-notes-with-optional-tags
**Contract:** contract-note-014 (Note GET response includes tag_names and tag_ids); app-state coordination via App.tsx selectedNoteId → EditorLayout → Editor loading flow
**Ready for review:** yes

**Approach:**

NoteList fetches all notes via GET /api/notes, renders them as clickable cards with title, body preview, tag badges (using stable tag_id keys), and created date. Clicking a note calls onEdit(noteId) which App.tsx uses to navigate to the editor with that noteId selected. Tags are displayed as small rounded badges, with conditional rendering to avoid empty badge sections when no tags exist. Loading, error, and empty states are all handled. Notes are reverse-chronological (as returned by backend).

**Files:**
- frontend/src/NoteList.tsx: new component file (249 lines); lists all notes with tag badges and click-to-edit handler
- frontend/src/App.tsx: modified to add selectedNoteId state, handleEditNote callback, and NoteList routing (added 19 lines, modified routing logic)
- frontend/src/EditorLayout.tsx: modified to accept noteId and onSave props, pass them to Editor (added 6 lines)
- frontend/src/Editor.tsx: modified to load existing note on mount if noteId provided, support PATCH updates, pass onSave callback to EditorLayout (added 62 lines)
- frontend/src/api.ts: unchanged (readNote and updateNote functions already present)

**Known Limitations:**
- Tag editing in NoteList view is not implemented (tags can only be added/edited in the editor); this is deferred as a v2 feature per Tweedledee's scope assessment. The backend supports it (tags are part of the note object and can be updated via PUT /api/notes/{id}); the NoteList UI does not expose the capability.
- Tag names with only whitespace (e.g., '  ') are accepted by the backend as valid tag names; normalization (trimming) is not yet enforced. This is tracked as a backend degradation item.
- Search feature integration is not yet complete (Search.tsx exists but hasn't been updated to use the search endpoint contract); deferred as separate feature work.
