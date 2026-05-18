## Ticket 035: Implement search endpoint with full-text matching

**GUID:** 01KRXX3SBC26W352THF856PJHT
**Sources:** kohl-searches-notes-by-title-and-body-content
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: kohl-search-results-ui
- Blocked by: kohl-note-crud-endpoints
- Soft: —

**Description:**

Create GET /api/notes/search?q=<query> endpoint that searches note titles and body content. Return matching notes with match locations highlighted for frontend rendering. Implement basic full-text matching (case-insensitive substring search v1; can upgrade to indexed FTS in fast-follow if perf requires). Accept empty query (return all notes); handle special characters gracefully.

**Acceptance:**
- GET /api/notes/search returns JSON array of matching notes
- Search matches title and body content (case-insensitive)
- Empty query returns all notes in storage order
- Endpoint handles 100+ notes without timeout
- Response includes note id, title, body, tags, and match context

**Risk:**

Performance on large note counts; if search is slow on >500 notes, expand to 3 days for SQLite FTS setup.
