## Review 008: Backend Note CRUD endpoints and model — implementation is correct and complete

**GUID:** 01KRXT3QP1KXYAN3TVS8RW3PNP
**Files reviewed:** src/backend/api/notes.py, src/backend/models.py
**Verdict:** accept

### Approvals

- All seven CRUD endpoints implemented per contract-note-003: POST /notes (201), GET /notes (200 list), GET /notes/{id} (200 single), PUT /notes/{id} (200 update), DELETE /notes/{id} (204), POST /notes/{id}/tags (200), DELETE /notes/{id}/tags/{tag_id} (204)
- Response shape exactly matches contracts: tag_names (string[]), tag_ids (int[]), timestamps as ISO8601 UTC with Z suffix
- Tag auto-creation is atomic — all tags created and associations made in a single transaction; missing tags are created on first POST/PUT
- Validation is precise: title required 1-255 chars, body optional max 16384, tag names 1-100 chars each. 422 for validation failures, 404 for missing resources, 204 for delete
- Timestamp handling is correct: server_default=func.now() on both columns, onupdate=func.now() on updated_at, to_dict() explicitly converts to UTC-aware ISO8601 with Z suffix
- Many-to-many relationship (note_tags junction table) is cleanly designed with cascade delete on both foreign keys
- Error responses distinguish between 'Note not found' and 'Tag not found', making debugging easier
