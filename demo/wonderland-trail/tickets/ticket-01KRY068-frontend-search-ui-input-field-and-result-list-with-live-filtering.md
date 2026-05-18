## Ticket 059: Frontend search UI: input field and result list with live filtering

**GUID:** 01KRY06830H13N52ZDNMW05R8K
**Sources:** kohl-searches-notes-by-title-and-body-content-for-rapid-rediscovery, 01KRXRFV251BRQPQMWQTZBXJSV:kohl-searches-notes-by-title-and-body-content, 01KRXRMEHCCPN14TM6J8PGJD7T:kohl-finds-a-past-note-by-title-or-content, 01KRXWRHF0MJX3M4TYVP2PEKP2:kohl-searches-notes-by-title-and-body-content
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: frontend-load-on-boot-integration-with-backend-notes-endpoint-and-localstorage-merge
- Soft: search-endpoint-full-text-index-and-query-on-notes-by-title-and-body

**Description:**

Build a React search interface component that accepts a query input field and displays results as a filterable note list. The search should trigger on keystroke (real-time filtering) rather than requiring an explicit search button. Display each result as a compact card showing note title, body preview (first 100 chars), tags, and updated_at timestamp. Integrate with the backend search endpoint (Story 025 backend ticket). Include empty-state messaging when no results match.

**Acceptance:**
- Search input field is visible and focusable in the app (as a distinct view or modal, location TBD in M3)
- On keystroke, the component calls GET /notes/search?q=[input] to the backend
- Results update in real-time with <300ms perceived latency (debounce if needed to avoid request spam)
- Each result displays: note title, first 100 chars of body, associated tags, and updated_at date
- Clicking a result navigates to (or opens in editor) the full note for viewing/editing
- When search input is cleared, the view returns to the note list (all notes in reverse-chronological order)
- Empty state messaging appears when no results match ('No notes found for [query]')
- No console errors; graceful handling of network timeouts (show spinner or error message)

**Risk:**

Search result highlighting (showing which words in the note matched the query) is not required for acceptance but would be nice-to-have. If the team adds it, estimate may expand to 2.5 days.
