## Implementation 044: Wildcard escaping in search queries + tag name normalization

**GUID:** 01KRXYY918GVFY4A7KPBZR9WPB
**Side:** backend
**Ticket:** ticket-053-test-allows-multiple-conflicting-outcomes-without-enforcing-one
**Contract:** GET /api/search contract-note-008 (search pattern with literal %, _); POST/PUT /api/notes contract-note-005 (tag_names normalized, whitespace-only rejected)
**Ready for review:** yes

**Approach:**

Added _escape_like_pattern() to escape SQL LIKE metacharacters (%, _) so user queries match literals, not wildcards. Updated search_notes() to use escape parameter. Added _normalize_and_validate_tag_names() to strip whitespace, reject empty strings, and deduplicate tags in all write paths (create_note, update_note, associate_tag).

**Invariants Enforced:**
- Tag names are normalized (leading/trailing whitespace stripped) before storage
- Empty or whitespace-only tag names are rejected at request boundary with HTTP 400
- SQL LIKE patterns escape % and _ so user queries match literal characters, not wildcards
- Tag deduplication prevents duplicate (exact-case) tags in a single note

**Schema Changes:**

None (tag normalization happens in application layer, not schema)

**Failure Modes Handled:**
- Whitespace-only tag input: returns 400 Bad Request, preserves prior state
- SQL wildcard in search query: treated as literal character (e.g., '100%' finds only '100%', not '100 percent')
- Duplicate tag names in request: deduplicated before association

**Files:**
- src/backend/api/notes.py: _escape_like_pattern(), search_notes() escape handling, _normalize_and_validate_tag_names(), _associate_tags() refactored to validate, create_note/update_note calls _associate_tags with validation

**Open Questions for Pair:**
- Tag case-sensitivity: current impl is case-sensitive ('Research' and 'research' are distinct tags). Contract-note-005 does not specify; should we normalize to lowercase for deduplication, or keep case-sensitive?

**Known Limitations:**
- Case-sensitivity not yet decided (see contract-note-005). Current: case-sensitive (three separate tags for 'research', 'Research', 'RESEARCH').
