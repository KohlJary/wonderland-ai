## Implementation 023: Backend search endpoint AND tag filtering validation

**GUID:** 01KRXW40RYN8EWQSM34FQWHPY7
**Side:** backend
**Ticket:** 01KRXVSVWD957YMT2Z4RX9QVDW
**Contract:** contract-note-008 (search-api/v1): GET /api/search with tags query parameter uses AND logic—notes matching ALL specified tags are returned
**Ready for review:** yes

**Approach:**

Verified that GET /api/search?tags=work,personal correctly implements AND logic for tag filtering. The search_notes function chains .filter() calls for each tag name, combining them with AND logic via SQLAlchemy. Query logic: parse comma-separated tag names, then for each tag_name, add a filter(Note.tags.any(Tag.name == tag_name)). Multiple filters are AND'd together, ensuring only notes with ALL specified tags are returned.

**Invariants Enforced:**
- Tag filtering uses AND logic: notes matching ALL specified tags are returned
- Multiple filter() calls are combined with AND via SQLAlchemy semantics
- Empty tag results return 200 with empty results array, not an error

**Schema Changes:**

None—existing note_tags many-to-many relationship unchanged

**Failure Modes Handled:**
- Non-existent tag IDs: return empty results (no error)
- Empty tag_names list: treated as no filter (all notes returned)
- Malformed tags parameter: empty strings stripped, handled gracefully

**Files:**
- src/backend/api/notes.py: search_notes endpoint with AND tag filtering logic verified

**Open Questions for Pair:**
- Are there any edge cases in tag filtering (e.g., whitespace handling, duplicate tag names in query) that need additional validation?

**Known Limitations:**
- Tag filtering is case-sensitive (matches exact tag names). If frontend needs case-insensitive tag matching, that would require a schema change.
