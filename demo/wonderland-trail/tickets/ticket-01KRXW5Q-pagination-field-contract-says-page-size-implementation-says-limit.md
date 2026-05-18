## Ticket 029: Pagination field: contract says 'page_size', implementation says 'limit'

**GUID:** 01KRXW5Q867M2ZJ7SHZ4XAQG42
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

From review ``feature-003-search-endpoint-contract-drift-on-api-shape`` (block):

**Concern:** Affects both the request (query parameter name) and response (field name) sides of the contract.

**Request:** Rename request parameter to 'page_size' (line 293) and response field to 'page_size' (line 325).

**Location:** ``src/backend/api/notes.py:293 (request), 325 (response)``

**Acceptance:**
- Rename request parameter to 'page_size' (line 293) and response field to 'page_size' (line 325).
