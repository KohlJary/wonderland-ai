## Implementation 026: Search endpoint contract alignment: parameter names, response fields, pagination indexing

**GUID:** 01KRXWBFW3Z8TFRJ1M9W3QMV9K
**Side:** backend
**Ticket:** ticket-01KRXW5Q7WXPHEFBXH9WTZPJRW (Query parameter name: contract says 'q', implementation says 'query')
**Contract:** contract-note-008 (search-api/v1): GET /api/search?q=<str>&tags=<comma-sep>&page=<int>&page_size=<int> returns {results: [SearchResultNote], total_results, page (1-indexed), page_size, has_more}
**Ready for review:** yes

**Approach:**

Fixed parameter and response field names to match contract-note-008 (search-api/v1): 'q' for text search query, 'page' (1-indexed, default 1), 'page_size' (default 20). Response uses 'total_results' and 'page_size'. Created SearchResultNote model to separate search results (with body_preview truncated to 150 chars) from full NoteResponse. All pagination logic uses 1-indexed pages: offset = (page - 1) * page_size.

**Invariants Enforced:**
- Text search is case-insensitive (ILIKE on title OR body)
- Tag filtering uses AND logic (notes must have ALL specified tags)
- Pagination is deterministic: ordered by updated_at DESC, then id DESC
- body_preview is always <= 150 characters (truncated at 150)
- total_results reflects all matching notes, not just current page

**Schema Changes:**

No schema changes. SearchResultNote is a new response model, not a database model.

**Failure Modes Handled:**
- Empty query: returns all notes (no filter applied)
- No matches: returns 200 with empty results array, total_results=0, has_more=false
- Invalid tag IDs: silently treated as empty filter (no notes match non-existent tags)
- Pagination beyond last page: returns empty results array with has_more=false
- Special characters in query: sanitized by ILIKE escaping, treated as literal characters

**Files:**
- src/backend/api/notes.py: Updated search_notes() parameter names and types, created SearchResultNote model, fixed pagination logic and response shape, updated docstrings

**Open Questions for Pair:**
- Frontend already aligned to contract-note-008 in api.ts and Search.tsx — no questions needed, contract is internally consistent

**Known Limitations:**
- Search results are read-only via the search endpoint (body_preview only, not full body). Clicking a result would require fetching full note via GET /api/notes/{id} if editing is desired (deferred to later feature).
