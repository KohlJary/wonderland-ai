## Scenario 197: Kohl types a search query, gets results, clicks a result to open it in the editor, then uses back button to return to search with query preserved

**GUID:** 01KRXYDVNXZN8XM83A00MPY619
**Severity:** silent-wrongness

**Setup:**

Kohl is on /search, the search input is empty and ready to type, no prior results are displayed

**Trigger:**

Kohl types 'rust' into the search input (debounced 300ms), waits for results to appear (3-5 results matching 'rust' in title or body), clicks the first result to open it in the editor

**Expected:**

The editor opens with the selected note fully loaded (title, body, tags visible). The browser history is intact so that pressing the back button returns to /search with the search query 'rust' still in the input field and the same results still displayed

**Concern:**

If the router does not preserve search state or query params in the URL, Kohl's back button will clear her query and reset the results. She loses context of what she was searching for. This is a degradation (the feature works, but the UX is worse than it should be)

**Property:**

search state survives navigation away and back
