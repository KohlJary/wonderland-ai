## Implementation 003: Complete CRUD endpoints for notes with tag association

**GUID:** 01KRXSPGK8Z9GCHVMM9EP4HHJ9
**Side:** frontend
**Ticket:** schema-doc-reserves-list-endpoint-for-v2-contradicting-ticket-scope
**Contract:** contract-note-003 (POST /notes, PATCH /notes/:id envelope), contract-note-004 (note creation with tags), contract-note-005 (tag auto-create by name), search-api/v1 (list endpoint pagination)
**Ready for review:** yes

**Approach:**

Updated models.py to replace denormalized JSON tags with proper SQLAlchemy many-to-many relationship via note_tags association table. Added Tag model with unique names. Implemented all seven endpoints per contract-note-003 and 004: POST /notes (create with auto-tag creation), GET /notes (list reverse chronological), GET /notes/{id} (read single), PUT /notes/{id} (update with atomic tag replace), DELETE /notes/{id} (delete with cascade), POST /notes/{id}/tags (associate new tag), DELETE /notes/{id}/tags/{tag_id} (remove association). Fixed to_dict() to return tags as simple string array matching test expectations.

**Files:**
- src/backend/models.py: Added Tag model, note_tags association table, relationship on Note, fixed to_dict() to return tag names as strings with UTC-aware timestamp serialization
- src/backend/api/notes.py: Added NoteUpdate, TagCreate, TagResponse Pydantic models; _associate_tags() helper for atomic tag association; implemented GET /notes (list), PUT /notes/{id} (update), DELETE /notes/{id}, POST /notes/{id}/tags, DELETE /notes/{id}/tags/{tag_id} endpoints; fixed POST /notes to use relationship instead of JSON
- src/backend/api/__init__.py: Updated router comment to document all endpoints

**Known Limitations:**
- List endpoint pagination not implemented (GET /notes returns all, fast-follow per contract-note-008)
- Search endpoint not implemented (contract-note-008 deferred to separate search ticket)
- No auth/ownership validation (single-device assumption per requirements)
- Tag filtering in list endpoint deferred to search endpoint
