## Ticket 077: Search backend: full-text index and query (POST /search)

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2Q
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-search-backend
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5-2 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: save-endpoint-atomic-writes

**Description:**

Implement GET /search?q=<query>. Use sqlite full-text search (FTS5) on notes title and body. User-scoped. Return note id, title, body preview (with match context), rank. On note save, update the FTS index.

**Acceptance:**
- GET /search?q=... returns ranked results
- Results are user-scoped
- FTS index is updated on note save
- Preview includes match context

**Risk:**

FTS schema tuning (tokenization, ranking algorithm) is unknown territory on this codebase. SQL complexity is moderate-to-high. Recommend pairing with Caterpillar for code review.
