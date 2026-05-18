## Ticket 030: Response body field: contract says 'body_preview' (150 chars), implementation sends full 'body'

**GUID:** 01KRXW5Q8ABXD6DQ15RAB7WP1Q
**Sources:** kohl-can-find-past-notes-by-title-or-content-search, feature-003-search-endpoint-contract-drift-on-api-shape
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``feature-003-search-endpoint-contract-drift-on-api-shape`` (change-required):

**Concern:** Performance: returning full note bodies in paginated search results wastes bandwidth. A search with 100 results sends 100x full bodies instead of 100x previews. The contract's optimization was intentional.

**Request:** Modify the search endpoint to return body_preview (150-char truncation) instead of full body. Either create a SearchResultNote response model (separate from NoteResponse) or conditionally exclude the body field in search results. Update frontend Search.tsx:153 to use note.body_preview.

**Location:** ``src/backend/api/notes.py:321 (NoteResponse reused in search results)``

**Acceptance:**
- Modify the search endpoint to return body_preview (150-char truncation) instead of full body. Either create a SearchResultNote response model (separate from NoteResponse) or conditionally exclude the body field in search results. Update frontend Search.tsx:153 to use note.body_preview.
