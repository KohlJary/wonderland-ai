## Ticket 027: Query parameter name: contract says 'q', implementation says 'query'

**GUID:** 01KRXW5Q7WXPHEFBXH9WTZPJRW
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

**Concern:** The contract is the canonical agreement between Tweedles. When code drifts from the contract, there are two conflicting sources of truth. Downstream consumers (third-party clients, documentation, future developers) won't know which to follow. This drift was silent—no review verified that the implementation matched the contract before shipping.

**Request:** Rename the parameter from 'query' to 'q' (line 292). This restores alignment with contract-note-008.

**Location:** ``src/backend/api/notes.py:292``

**Acceptance:**
- Rename the parameter from 'query' to 'q' (line 292). This restores alignment with contract-note-008.
