## Contract Note 008: Search endpoint contract: GET /api/search with pagination

**GUID:** 01KRXRWWWCV2P0NZ99P1BCRBQR
**State:** agreed
**Contract Version:** search-endpoint-contract-get-api-search-with-pagination/v1

**Current Shape:**

n/a, fresh feature

**Proposed Change:**

GET /api/search?q=<search text>&tags=<comma-sep tag IDs or names>&page=<int>&page_size=<int>. Returns: {"total_results": int, "page": int, "page_size": int, "results": [{"id": int, "title": str, "body_preview": str (first 100 chars, per contract-note-search-response-envelope v1), "tags": [{"id": int, "name": str}, ...], "created_at": ISO8601}, ...]}. Status 200 success; 400 invalid params; 500 server error.

**Source:** ticket-01KRXRQZ (both backend and frontend search tickets), story kohl-finds-a-past-note-by-title-or-content; requirement substring-search-across-note-titles-bodies-and-tags

**Frontend Impact (Tweedledee):**

I will render a search form with text input (onChange sends debounced requests) and tag multiselect filter. Results display as a paginated list, each row showing title, preview, tags, created_at. Pagination: prev/next buttons or infinite scroll (depends on UX, but pagination controls need total_results + page metadata to work). Clicking a result opens that note in the editor. Clearing the search returns to the main notes list. Error handling: 4xx shows user-facing message; 5xx shows 'server error, please try again'. Tag filter can send either tag IDs or tag names — need to know which you prefer on backend.

**Backend Impact (Tweedledum):**

GET /api/search endpoint with FTS5 full-text search on note title+body. Query params: `q` (string, 1–200 chars, required), `tags` (comma-separated tag IDs or names, optional, AND logic if multiple), `page` (int ≥ 1, default 1), `page_size` (int 1–100, default 20). Returns 200 with shape {total_results, page, page_size, results: [...]}, or 400 if params invalid, or 500 on server error.

Implementation: FTS5 virtual table (created in schema migration, synced with note title+body on every note write). Tag filtering via note_tags JOIN table (if tags provided, note must have all specified tags). Tag names and IDs both supported (query resolves names to IDs before filtering).

Invariants enforced: (1) FTS5 index stays synchronized with note content (any note write invalidates cache); (2) pagination bounds validated server-side; (3) tag filters reference existing tags only (non-existent IDs silently return empty results, no error).

Failure modes: (1) FTS5 query syntax errors → sanitize input (strip special chars, wrap in quotes); (2) tag_ids containing non-existent IDs → treat as empty filter; (3) empty search results → return {total_results: 0, ...} with empty results array.

**Resolution:**

Covered by contract-note-01KRXRWW (agreed). Search is in v1 scope and ready for client integration. No further backend work needed.
