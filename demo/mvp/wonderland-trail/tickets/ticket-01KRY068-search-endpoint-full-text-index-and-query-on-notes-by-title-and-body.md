## Ticket 058: Search endpoint: full-text index and query on notes by title and body

**GUID:** 01KRY06830H13N52ZDNMW05R8J
**Sources:** kohl-searches-notes-by-title-and-body-content-for-rapid-rediscovery, 01KRXRFV251BRQPQMWQTZBXJSV:kohl-searches-notes-by-title-and-body-content, 01KRXRMEHCCPN14TM6J8PGJD7T:kohl-finds-a-past-note-by-title-or-content, 01KRXWRHF0MJX3M4TYVP2PEKP2:kohl-searches-notes-by-title-and-body-content
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5–2.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: replace-hellomessage-scaffolding-with-note-model, note-and-tag-schema-with-crud-endpoints
- Soft: —

**Description:**

Implement a GET /notes/search?q=query endpoint that returns notes matching the search term in title or body (case-insensitive substring match). Build the search on top of SQLite's FTS5 (full-text search) module if available, or fallback to LIKE queries if FTS5 is not viable. The endpoint must return results in reverse-chronological order (most recently edited first) and be performant for ~500 notes (target sub-500ms latency). No pagination required for v1, but the response schema should anticipate it.

**Acceptance:**
- GET /notes/search?q=transformer accepts a query string and returns notes matching that term in title or body
- Search is case-insensitive and performs substring matching (searching 'attention' finds 'attention-head variance')
- Results are ordered by updated_at descending (most recently edited first)
- Response includes note id, title, body preview (first 150 chars), tags, and updated_at for each match
- Search latency is sub-500ms for typical queries against a ~100-note corpus (measured locally)
- Empty or missing query returns all notes in reverse-chronological order (or 400 Bad Request — contract to decide)
- No console errors; graceful handling of SQLite errors (malformed query, etc.)

**Risk:**

FTS5 availability in the SQLite version — if not available, fallback to LIKE will be slower. Estimate may expand to 3 days if optimization is needed.
