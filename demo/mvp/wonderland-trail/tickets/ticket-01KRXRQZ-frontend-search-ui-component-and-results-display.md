## Ticket 013: Frontend search UI component and results display

**GUID:** 01KRXRQZTACDF3MZ9AWN6NZYJH
**Sources:** kohl-can-find-past-notes-by-title-or-content-search, story-kohl-can-find-past-notes-by-title-or-content-search
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: backend-search-endpoint-for-notes-by-title-and-content
- Soft: —

**Description:**

Build a search form component with text input and tag multiselect filter. Display paginated results in a list with note title, content preview, tags, and created date. Support clearing search and returning to the main notes list. Wire to the backend search endpoint.

**Acceptance:**
- Search form renders with text input and tag filter UI
- Submits query to backend endpoint and displays results
- Results show note title, content preview, tags, date
- Pagination controls work; user can navigate result pages
- Clear search button resets form and returns to main notes view
- Search results update in real-time as user types (if debounced)

**Risk:**

Tag multiselect UI complexity if tag count grows; may need virtualization for large tag lists. Coordinate with Tweedledum on pagination contract.
