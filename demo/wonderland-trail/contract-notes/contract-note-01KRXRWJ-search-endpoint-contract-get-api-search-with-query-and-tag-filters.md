## Contract Note 007: Search endpoint contract: GET /api/search with query and tag filters [SUPERSEDED BY 008]

**GUID:** 01KRXRWJB1TXB1A8R6ETTSP3V1
**State:** counterpart_assessed
**Contract Version:** (superseded by search-api/v1 in contract-note-008)

**Current Shape:**

No search endpoint exists yet; existing CRUD endpoints are: POST /api/notes (create), GET /api/notes (list all), GET /api/notes/{id} (read one), PUT /api/notes/{id} (update), DELETE /api/notes/{id} (delete). Pagination exists on listing but not formalized.

**Proposed Change:**

Add GET /api/search endpoint. Query shape: query_string (text search on title + body, case-insensitive substring), tag_ids (optional array of tag IDs to filter by, AND logic if multiple). Response shape: paginated result with page/limit/total counts, array of note summaries (id, title, body_preview_200chars, tags, created_at, updated_at). Implementation: SQLite full-text search (FTS5) on title+body, filtered by tag_ids via JOIN if provided.

**Source:** ticket-backend-search-endpoint-for-notes-by-title-and-content; ticket-frontend-search-ui-component-and-results-display. Both acceptance criteria require clarity on pagination format and result shape before frontend can wire to it.

**Frontend Impact (Tweedledee):**

Search component: text input with debounced ~300ms query submission + tag multiselect filter UI. Submits query_string + tag_ids array to GET /api/search endpoint. Results display as paginated list (20 per page, prev/next navigation). Each result item shows: title, body_preview, tags, created_at. On your two questions: (1) 200-char body preview is exactly right for Kohl's use case — she scans many notes looking for context, and a 200-char snippet is enough to jog her memory without overwhelming the results list. (2) Tags inline in the result object is better than separate hydration — single round-trip UX is superior, and tag count per note is typically small so payload is not a concern. Frontend state: search term + current page live in React component state (useState). No localStorage persistence for search params — search is a discovery flow, not a persistent artifact. UI states implemented: search-form-ready, loading-results, results-empty, results-display, error-recoverable (if search request fails, show 'search failed; please try again', allow retry). Real-time-as-you-type is acceptable if backend can handle ~3-5 req/sec per user at peak (debounce on client). If that's too aggressive, I can add an explicit 'Search' button to require user action. Your call.

**Backend Impact (Tweedledum):**

New endpoint GET /api/search(query: str, tag_ids: List[int], page: int = 1, limit: int = 20). Implementation requires: (1) FTS5 virtual table mirroring note title+body (created during schema migration), (2) query validation (min 1 char, max 200 chars), (3) pagination validation (page >= 1, 1 <= limit <= 100), (4) tag filtering via note_tags JOIN (if tag_ids provided, AND logic — note must have all specified tags). Returns: {total: int, page: int, limit: int, results: [{id, title, body_preview, tags: [{id, name}], created_at, updated_at}]}. Performance constraint: FTS5 index keeps search fast even at 1000+ notes; SQLite can handle this. Failure mode: if tag_ids contains non-existent IDs, return empty results (no error — treats as 'no notes match this filter').
