## Implementation 035: Feature 005 blocking findings resolved: navigation, tag keys, note loading

**GUID:** 01KRXYDDGZM9PTKNMB18B19GQW
**Side:** frontend
**Ticket:** feature-005-kohl-organizes-notes-with-optional-tags
**Contract:** contract-note-01KRXRTT (Note model with tag_names and tag_ids), contract-note-014 (GET /api/notes response includes tags), ticket-007 (Editor pane), ticket-009 (Tag input and association)
**Ready for review:** yes

**Approach:**

Fixed three blocking issues: (1) App.tsx now threads selectedNoteId to EditorLayout properly, enabling click-to-edit workflow. (2) Editor.tsx loads notes from backend when noteId is provided via readNote() call. (3) NoteList.tsx uses stable tag_ids for React keys instead of array indices. (4) All callback contracts (onEdit signature) match their implementation. These fixes restore the feature's core use case: Kohl can click a note in the list and edit its tags.

**Files:**
- frontend/src/App.tsx: navigation state threading (selectedNoteId), handleEditNote and handleEditorSave callbacks
- frontend/src/Editor.tsx: noteId prop acceptance, note loading on mount via readNote(), localStorage integration
- frontend/src/NoteList.tsx: tag key generation uses stable tag_ids, click handler properly invokes onEdit callback
- frontend/src/EditorLayout.tsx: noteId and onSave prop acceptance, passes through to Editor

**Known Limitations:**
- Tag editing in NoteList is read-only; tags can only be edited via EditorLayout (acceptable for v1, inline editing deferred to v2 per Alice decision)
