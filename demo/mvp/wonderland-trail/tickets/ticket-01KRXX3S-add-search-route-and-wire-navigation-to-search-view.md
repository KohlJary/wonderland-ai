## Ticket 037: Add search route and wire navigation to search view

**GUID:** 01KRXX3SBC26W352THF856PJHW
**Sources:** kohl-searches-notes-by-title-and-body-content
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: kohl-search-results-ui
- Soft: —

**Description:**

Add search route to React router (e.g. /notes/search or /search). Create search page component that houses search input + results list. Add navigation link from main notes view to search. Ensure back button returns to notes list, not lost.

**Acceptance:**
- Search route is reachable from notes view
- Search page loads with input ready to type
- Back navigation returns to notes view with state intact
- Search persists across page reload (input + results in URL params or local state)

**Risk:**

Low. Router setup is standard React; state management depends on existing nav patterns.
