## Implementation 017: Search endpoint with text and tag filtering

**GUID:** 01KRXVRHPJH7J8ZH6KAFGE0QDQ
**Side:** backend
**Ticket:** ticket-016
**Contract:** contract-note-002: SearchResponse {results: NoteResponse[], total: int, page: int, limit: int, has_more: bool}; query params: query (optional text), tags (optional comma-separated), page (default 0, ge=0), limit (default 20, ge=1, le=100)
**Ready for review:** yes

**Approach:**

Added GET /api/search endpoint that performs case-insensitive substring match on title and body (OR logic), filters by comma-separated tag names (OR logic — any tag matches), and returns paginated results. Search query is case-insensitive via SQLAlchemy's ilike(). Tag filtering builds cumulative filters with Note.tags.any(Tag.name == tag_name) which applies OR semantics. Pagination uses OFFSET/LIMIT with total count for has_more calculation. Results ordered by updated_at DESC then id DESC for determinism.

**Invariants Enforced:**
- Text search is case-insensitive: SQLAlchemy ilike() converts both query and target to same case before comparison
- Results ordered by updated_at DESC, then id DESC: ensures stable pagination across concurrent updates
- Tag filtering uses tag NAMES not IDs: query parameter is 'tags' (comma-separated names), not tag IDs
- Pagination respects LIMIT and OFFSET: calculated as offset = page * limit, respects database cursor bounds
- Total count includes all matching notes: counted before LIMIT/OFFSET, not after, so has_more is accurate

**Schema Changes:**

No schema changes — uses existing Note, Tag, and note_tags tables.

**Failure Modes Handled:**
- Empty query parameter: returns all notes (no filtering)
- Nonexistent tag in tags parameter: returns empty results (no error)
- Invalid page/limit: FastAPI validation rejects before endpoint runs (ge/le constraints)
- No matching notes: returns SearchResponse with empty results array, total=0, has_more=false
- Special characters in query (%, _, quotes): passed to SQLite LIKE as-is (potential wildcard matches, not escaped)

**Files:**
- src/backend/api/notes.py: added SearchResponse model, search_notes() endpoint (82 lines), updated module docstring with search contract

**Open Questions for Pair:**
- Tag filtering semantics: implementation uses OR (any tag matches). Contract comment says 'AND logic' but test cases (test_tag_filtering_with_multiple_tag_names) verify OR. Confirm this matches frontend expectations or I can pivot to AND.

**Known Limitations:**
- Tag filtering is OR semantics (any specified tag matches), not AND. If Tweedledee needs AND (all tags must match), implementation needs one-line change to loop logic.
- LIKE wildcard escaping not explicitly handled for % or _ in search query — SQLite treats these as wildcards. If literal % search is needed, would need ESCAPE clause.
- Pagination limit capped at 100 per FastAPI validation; if deeper browsing needed, would require larger limit cap.
