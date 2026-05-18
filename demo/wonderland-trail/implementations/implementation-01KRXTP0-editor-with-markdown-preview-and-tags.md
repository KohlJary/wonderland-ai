## Implementation 010: Editor with markdown preview and tags

**GUID:** 01KRXTP0MQ00A8A21XGT1W8TZ0
**Side:** frontend
**Ticket:** 007-008-009
**Contract:** message-envelope v3 per contract-note-01KRXRTT: POST /api/notes {title: str, body?: str, tag_names?: str[]} → {id, title, body, tag_names, tag_ids, created_at, updated_at}. GET /api/notes/{id} → same. PUT /api/notes/{id} → same. DELETE /api/notes/{id} → 204.
**Ready for review:** yes

**Approach:**

Editor component handles title input (max 255 chars, required on save), markdown body textarea (max 16384 chars, optional), and TagInput for adding/removing tags. On save, POST /api/notes with {title, body, tag_names}. Keystroke buffer to localStorage on every change; restored on mount; cleared after successful save. Preview component renders markdown→HTML with DOMPurify sanitization. TagInput allows add-by-Enter or Add button; prevents duplicates; displays tags as removable chips.

**UI States Implemented:**
- loading: spinner shown during POST /api/notes (save button disabled, form disabled)
- empty: initial editor state (title empty, body empty, tags empty)
- error-recoverable: save failed (error message shown, state preserved, user can retry)
- success: note saved (success message shown, editor cleared, localStorage cleared)
- preview: Preview pane renders live markdown as user types (EditorLayout only)

**Client State:**

localStorage keystroke buffer (editor_draft key) stores {title, body, tags} as JSON string. On mount, restore to editor state if buffer exists. On every keystroke in title/body or tag change, write buffer immediately. On successful save, clear buffer and reset editor to empty state. This ensures user can recover partially-written notes if they accidentally close the tab. Canonical state is server-side after save; client-side buffer is ephemeral draft only.

**Files:**
- frontend/src/Editor.tsx: title + body + tag inputs, localStorage keystroke buffer, save handler
- frontend/src/Preview.tsx: markdown parsing (marked library), XSS sanitization (DOMPurify)
- frontend/src/TagInput.tsx: tag chip input + display, add/remove handlers, duplicate prevention
- frontend/src/api.ts: createNote, listNotes, readNote, updateNote, deleteNote bindings
- frontend/src/App.tsx: mounts Editor component
- frontend/src/EditorLayout.tsx: wires Editor + Preview side-by-side (for v2 adoption)
- frontend/package.json: added marked + dompurify dependencies

**Open Questions for Pair:**
- Should Editor display created_at / updated_at timestamps in the UI after save, or is the note ID + success message sufficient for the user?
- The Editor currently supports creating new notes; should v1 also support editing existing notes (GET /api/notes/{id} → prefill), or is create-only the v1 scope?

**Known Limitations:**
- Note listing: Editor creates notes but cannot browse existing notes; v1.1 or v2 will add GET /api/notes UI.
- Editing: cannot fetch and edit an existing note by ID; create-only in v1.
- Markdown syntax highlighting: code blocks render but have no syntax highlighting; deferred to v2.
- Mobile layout: Editor + Preview layout is desktop 50/50 split; stacked layout for mobile deferred to v2.
- Tag management: no way to browse all tags or filter notes by tag; tag search deferred to v2.
