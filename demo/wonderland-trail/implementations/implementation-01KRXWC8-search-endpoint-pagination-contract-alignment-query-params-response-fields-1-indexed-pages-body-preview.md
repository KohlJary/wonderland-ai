## Implementation 028: Search endpoint pagination contract alignment (query params, response fields, 1-indexed pages, body_preview)

**GUID:** 01KRXWC8DGWQSK7HEW2QXB2EGP
**Side:** backend
**Ticket:** ticket-01KRXW5Q
**Contract:** search-api/v1 per contract-note-01KRXRWW: GET /api/search?q=...&tags=...&page=...&page_size=... returns {results: SearchResultNote[], total_results: int, page: int (1-indexed), page_size: int, has_more: bool}
**Ready for review:** yes

**Approach:**

Modified src/backend/api/notes.py to: (1) Rename query parameter 'q' (was 'query'), (2) Add SearchResultNote model for search results with body_preview field (150-char truncation), (3) Change SearchResponse fields: total→total_results, limit→page_size, (4) Rename Query parameter page_size (was 'limit'), (5) Change pagination from 0-indexed (default 0) to 1-indexed (default 1, ge=1), (6) Updated pagination calculation from offset=page*page_size to offset=(page-1)*page_size

**Invariants Enforced:**
- page parameter is 1-indexed (ge=1, default 1) per contract
- page_size parameter is capped at 100 (le=100) per contract
- body_preview is always <= 150 chars (truncated at 150 for search results optimization)
- Query parameter 'q' (not 'query') for text search per contract
- Response field names match contract: total_results (not total), page_size (not limit)

**Schema Changes:**

No schema changes — purely contract field name and pagination semantic changes

**Failure Modes Handled:**
- Page out of bounds (beyond total_results): returns empty results with has_more=false
- Empty search results: returns valid SearchResponse with empty results array, total_results=0, has_more=false
- Invalid page_size or page values: rejected with 422 validation error

**Files:**
- src/backend/api/notes.py: Added SearchResultNote model, updated SearchResponse model, renamed query parameters and response fields, changed pagination to 1-indexed, added body_preview truncation logic
- frontend/src/api.ts: Updated SearchResponse and SearchResultNote interfaces to match backend contract changes, updated searchNotes() function default values and parameter names
