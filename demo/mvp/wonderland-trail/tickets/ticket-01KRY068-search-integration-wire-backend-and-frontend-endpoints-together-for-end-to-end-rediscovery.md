## Ticket 060: Search integration: wire backend and frontend endpoints together for end-to-end rediscovery

**GUID:** 01KRY06830H13N52ZDNMW05R8M
**Sources:** kohl-searches-notes-by-title-and-body-content-for-rapid-rediscovery, 01KRXRFV251BRQPQMWQTZBXJSV:kohl-searches-notes-by-title-and-body-content, 01KRXRMEHCCPN14TM6J8PGJD7T:kohl-finds-a-past-note-by-title-or-content, 01KRXWRHF0MJX3M4TYVP2PEKP2:kohl-searches-notes-by-title-and-body-content
**Owner:** either
**Tier:** v1
**Stack span:** full-stack
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: search-endpoint-full-text-index-and-query-on-notes-by-title-and-body, frontend-search-ui-input-field-and-result-list-with-live-filtering
- Soft: —

**Description:**

Integration ticket: ensure backend search endpoint and frontend search UI are contract-aligned. Verify that the backend returns response shape the frontend expects, that error handling is consistent (400 for bad query, 500 for server error), and that the frontend gracefully handles network timeouts. This ticket is small — mostly verification and minor schema alignment. The actual endpoint and UI are delivered by the prior two tickets.

**Acceptance:**
- Backend endpoint and frontend client agree on request/response schema (query param name, response shape, error codes)
- Frontend successfully calls backend search endpoint and displays results without client-side parsing errors
- Error handling: 400 from backend (bad query) shows a user-facing error message in frontend
- Error handling: 500 from backend shows a generic error message (not a stack trace)
- Network timeout (backend unreachable) is handled gracefully: frontend shows 'Unable to search — try again' message
- End-to-end test: user types 'transformer' in search, sees matching notes within 1 second
- Logging: both backend and frontend log search queries (for audit/debugging)

**Risk:**

Low risk. This is mostly validation work; the two tickets above do the heavy lifting.
