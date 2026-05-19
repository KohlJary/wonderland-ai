## Ticket 036: Build search results UI with query input and match highlighting

**GUID:** 01KRXX3SBC26W352THF856PJHV
**Sources:** kohl-searches-notes-by-title-and-body-content
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-1.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: kohl-search-endpoint
- Soft: kohl-markdown-preview

**Description:**

Create search UI: text input field for query, results list showing title + excerpt with highlighted matches, click-to-view for each result. Wire to search endpoint. Show result count. Handle empty state (no matches) gracefully. Preserve search input across navigation so user can refine without retyping.

**Acceptance:**
- Search input visible on notes view (or dedicated search page)
- Query submission triggers API call and displays results within 200ms
- Results highlight matching keywords in title and body excerpt
- Clicking a result opens full note view
- Empty state message appears when no matches found
- Search input clears when user navigates away and back

**Risk:**

Highlighting implementation; if regex escaping for special chars in query becomes complex, add 4-6 hours.
