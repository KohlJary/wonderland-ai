## Ticket 031: Pagination indexing: contract says 1-indexed (default 1), implementation says 0-indexed (default 0)

**GUID:** 01KRXW5Q8FR9XMH0C1WMHGC1GG
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

**Concern:** Pagination indexing is part of the contract. The implementation chose 0-indexed without re-negotiating the contract.

**Request:** Change to 'page: int = Query(default=1, ge=1, ...)' and adjust offset calculation from 'page * limit' to '(page - 1) * limit' in the search function.

**Location:** ``src/backend/api/notes.py:293``

**Acceptance:**
- Change to 'page: int = Query(default=1, ge=1, ...)' and adjust offset calculation from 'page * limit' to '(page - 1) * limit' in the search function.
