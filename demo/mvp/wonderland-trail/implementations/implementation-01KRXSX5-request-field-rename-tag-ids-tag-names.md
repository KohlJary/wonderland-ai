## Implementation 005: Request field rename: tag_ids → tag_names

**GUID:** 01KRXSX54KPYX3MVDBZG36DA35
**Side:** backend
**Ticket:** request-field-mismatch-tag-ids-vs-tag-names
**Contract:** message-envelope v2 (tag_names: string[] in POST/PUT /api/notes request bodies)
**Ready for review:** yes

**Approach:**

Updated Pydantic request models NoteCreate and NoteUpdate to use field name tag_names instead of tag_ids. Updated all docstrings and endpoint handler references. The internal _associate_tags function already expected tag names; no changes needed there.

**Invariants Enforced:**
- tag_names field contains strings (tag names), not integers (tag IDs)

**Schema Changes:**

None (Pydantic model field rename only; database schema unchanged)

**Files:**
- src/backend/api/notes.py: NoteCreate model field rename, NoteUpdate model field rename, module docstring contract update, create_note endpoint handler, update_note endpoint handler
