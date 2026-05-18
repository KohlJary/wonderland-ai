## Ticket 028: Response field: contract says 'total_results', implementation says 'total'

**GUID:** 01KRXW5Q81YQVN978TY9YZWJ7J
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

**Concern:** Response field names are part of the HTTP API contract. Drift means any client expecting 'total_results' will receive a response with 'total' instead and fail to parse it.

**Request:** Rename the field to 'total_results' (line 321).

**Location:** ``src/backend/api/notes.py:321``

**Acceptance:**
- Rename the field to 'total_results' (line 321).
