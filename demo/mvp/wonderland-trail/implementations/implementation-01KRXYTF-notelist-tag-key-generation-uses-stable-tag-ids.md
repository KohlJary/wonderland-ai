## Implementation 039: NoteList tag key generation uses stable tag_ids

**GUID:** 01KRXYTFKNWVD641VPZ1A3PJ7A
**Side:** frontend
**Ticket:** ticket-01KRXY8N-tag-key-generation-uses-array-index-instead-of-stable-tag-id
**Contract:** contract-note-014 (GET /api/notes and /notes/{id} response includes tag_names and tag_ids) — both arrays parallel and order-preserved
**Ready for review:** yes

**Approach:**

NoteList.tsx iterates over note.tag_ids with array index, reads corresponding tag_names[index], and uses tag-${tagId} as React key. Backend contract (api.ts Note interface) guarantees tag_ids[i] corresponds to tag_names[i] in order.

**UI States Implemented:**
- notes-list-with-tags
- notes-list-no-tags
- notes-list-empty
- notes-list-loading
- notes-list-error

**Client State:**

notes: Note[], loaded and displayed in reverse chronological order per backend contract. Tag state is read-only in NoteList (tags cannot be edited inline; edit flow requires opening EditorLayout).

**Files:**
- frontend/src/NoteList.tsx:93-102: tag rendering loop uses tag_ids.map with stable key instead of array index
