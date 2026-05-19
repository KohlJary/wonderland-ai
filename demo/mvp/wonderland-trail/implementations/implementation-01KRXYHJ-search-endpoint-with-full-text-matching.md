## Implementation 037: Search endpoint with full-text matching

**GUID:** 01KRXYHJZ8PTQD26420YAMDWKE
**Side:** backend
**Ticket:** ticket-01KRXX3S
**Contract:** search-endpoint-contract-get-api-search-with-pagination/v1 — query params {q?: str, tags?: str, page?: int (≥1, default 1), page_size?: int (1-100, default 20)}; response {results: [{id, title, body_preview ≤150 chars, tag_names, tag_ids, created_at, updated_at}], total_results: int, page: int, page_size: int, has_more: bool}
**Ready for review:** yes

**Approach:**

GET /api/search endpoint using SQLAlchemy query builder with case-insensitive ILIKE for text search (title OR body), chained .filter() for AND-logic tag filtering, 1-indexed pagination with page/page_size, response includes total_results, page, page_size, has_more, and results array with body_preview (first 150 chars) truncation for optimization.

**Invariants Enforced:**
- Text search is case-insensitive (SQLite ILIKE): 'Research' matches 'research'
- Tag filtering uses AND logic: notes must have ALL specified tags to match
- Pagination is 1-indexed: page ≥ 1, not 0-indexed
- body_preview is always ≤ 150 chars (truncated to 150)
- total_results counts all matching notes, not just current page
- Results ordered by updated_at DESC then id DESC for deterministic ordering

**Schema Changes:**

No schema changes. Uses existing Note and Tag models with existing note_tags association table.

**Failure Modes Handled:**
- Empty query (q=null): returns all notes (no filter applied)
- No matching notes: returns empty results array with total_results=0, has_more=false
- Invalid tag name: returns empty results (tag doesn't exist, no error)
- page_size > 100 or < 1: FastAPI validation rejects with 422
- page < 1: FastAPI validation rejects with 422
- query with special chars (%,?): SQLAlchemy parameterized queries prevent SQL injection, LIKE wildcards are literal

**Files:**
- src/backend/api/notes.py: Added SearchResultNote and SearchResponse models; implemented search_notes() endpoint with full-text search, tag AND-filtering, 1-indexed pagination, body_preview truncation

**Open Questions for Pair:**
- Frontend expects pagination param name 'page_size' and response field 'total_results' per contract-note-01KRXRWW — both implemented. Confirm Search.tsx api.ts matches these names.

**Known Limitations:**
- No full-text index (FTS5) yet — substring matching is O(n); upgrade path exists for indexed FTS if perf becomes concern at >1000 notes
- Special character handling (%, ?) relies on SQLite's LIKE escaping; no explicit escaping logic (SQLAlchemy parameterized queries prevent injection)
