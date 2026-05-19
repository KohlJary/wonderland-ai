## Ticket 012: Backend search endpoint for notes by title and content

**GUID:** 01KRXRQZT9TMZW9NS81WZ77JAG
**Sources:** kohl-can-find-past-notes-by-title-or-content-search, story-kohl-can-find-past-notes-by-title-or-content-search
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-search-ui-component-and-results-display
- Blocked by: backend-note-schema-definition-with-sqlite-migrations, backend-note-and-tag-crud-endpoints-with-schema
- Soft: —

**Description:**

Implement a GET /api/search endpoint that accepts query parameters for text search (title and content) and tag filtering. Return paginated results with note metadata. Search should be case-insensitive substring match on title and content fields.

**Acceptance:**
- GET /api/search accepts query and tag parameters
- Returns paginated results with title, content snippet, tags, created_at
- Case-insensitive substring matching on title and content
- Tag filtering works correctly when provided
- Endpoint documented in API contract

**Risk:**

SQLite full-text search performance on large note sets; may need index tuning or query optimization if test data grows beyond 1000 notes.
