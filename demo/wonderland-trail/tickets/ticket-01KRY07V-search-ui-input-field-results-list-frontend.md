## Ticket 076: Search UI: input field + results list (frontend)

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2P
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-search-ui
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.75-1.25 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: search-backend-implementation

**Description:**

Add search input field to note list view. On keystroke, call GET /search?q=<query>. Display results as a filtered list (title + preview + match highlight). Debounce input to avoid hammering backend. Show 'no results' state when query returns empty.

**Acceptance:**
- Search input is present and visible
- Query is debounced before backend call
- Results are displayed with title + preview
- Match highlights are visible
- Empty state is handled gracefully

**Risk:**

UX polish on highlight rendering may require iteration.
