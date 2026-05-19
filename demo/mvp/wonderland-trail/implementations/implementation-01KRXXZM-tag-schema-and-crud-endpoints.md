## Implementation 030: Tag schema and CRUD endpoints

**GUID:** 01KRXXZM4NDYHPYKHRDY90J2GH
**Side:** backend
**Ticket:** add-tag-schema-and-crud-endpoints
**Contract:** message-envelope v2 (note response includes tag_names: str[], tag_ids: int[])
**Ready for review:** yes

**Approach:**

SQLAlchemy models: Tag with unique name constraint; note_tags association with CASCADE on note_id, non-CASCADE on tag_id to preserve tags when notes are deleted. Endpoints: POST /api/notes/{id}/tags (auto-create tag if missing, idempotent), DELETE /api/notes/{id}/tags/{tag_id} (remove association), GET returns tag lists (tag_names array + tag_ids array). Search filters by tags with AND logic (notes matching ALL specified tags). All note mutations return updated tag lists.

**Invariants Enforced:**
- Tag.name is globally unique (database UNIQUE constraint)
- Note-tag associations are atomic (transactional, all-or-nothing in _associate_tags)
- Duplicate associations are prevented (checked before note.tags.append)
- Tags persist when notes are deleted (foreign key on tag_id has no ondelete CASCADE)
- POST /api/notes/{id}/tags is idempotent (appends only if not already associated)
- Search pagination is deterministic (secondary sort by id DESC after updated_at DESC)
- Body preview in search is truncated to 150 chars

**Schema Changes:**

CREATE TABLE tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) NOT NULL UNIQUE); CREATE TABLE note_tags (note_id INTEGER PRIMARY KEY FOREIGN KEY (notes.id) ON DELETE CASCADE, tag_id INTEGER PRIMARY KEY FOREIGN KEY (tags.id)). Migrations use Base.metadata.create_all on startup (SQLite dev mode; would use Alembic in production). Backward-compatible: adds schema only, does not alter existing note columns.

**Failure Modes Handled:**
- Tag already exists when auto-creating: query-then-create-or-fetch pattern catches duplicate and reuses existing tag
- Duplicate association attempt: checked via 'if tag not in note.tags' before append (idempotent)
- Note not found on POST /tags or DELETE /tags/{id}: return 404
- Tag not found on DELETE /notes/{id}/tags/{tag_id}: return 404
- Tag not associated with note: return 404 on DELETE (explicit validation)

**Files:**
- src/backend/models.py: Tag class (id, name with unique=True), note_tags association table (CASCADE on note_id only)
- src/backend/api/notes.py: POST /api/notes/{id}/tags, DELETE /api/notes/{id}/tags/{tag_id}, search filtering by tags

**Known Limitations:**
- Tag names are case-sensitive (e.g., 'Research' and 'research' are separate tags). Users may expect case-insensitive dedup; document or implement normalization if desired.
- Whitespace-only tag names (e.g., '  ') are currently accepted. Consider validating tag_name to reject empty or whitespace-only strings.
