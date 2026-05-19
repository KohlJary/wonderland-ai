## Scenario 194: Kohl searches with an empty query and sees all notes or an 'enter search term' message

**GUID:** 01KRXYDGJMBMVN3X0NM5ETQ1NX
**Severity:** degradation

**Setup:**

Kohl is on the search page. She hasn't typed anything in the search box yet (query is empty string).

**Trigger:**

Kohl waits for the 300ms debounce (or explicitly submits an empty query).

**Expected:**

One of two outcomes: (A) the search returns all notes in reverse chronological order (showing her full note list), or (B) the search page shows a message like 'Enter a search term to begin' and no results list. Either is acceptable; the behavior should be explicit.

**Concern:**

If empty search crashes the backend or returns a 400 error, Kohl cannot use search as a way to browse all notes. If empty search is silently ignored and stale results remain from the prior query, Kohl may not realize the query reset.

**Property:**

empty-search-query-must-either-return-all-notes-or-show-explicit-no-query-message
