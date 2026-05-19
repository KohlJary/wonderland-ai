## Scenario 220: Kohl searches for 'attention', sees matching notes, clicks one, and the note opens in the editor without losing her search state

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HX9
**Severity:** degradation

**Setup:**

Kohl has a note titled 'Attention: Mutation Detection' and another note with 'attention' in the body. She's on the Search view with 'attention' typed in the search input and results displayed.

**Trigger:**

Kohl clicks on one of the search results to open that note in the editor for viewing or editing.

**Expected:**

The editor opens with the selected note's content (title, body, tags). When Kohl navigates back to the Search view (via back button or navigation menu), the search input still contains 'attention' and the results are still displayed as they were before she clicked. Kohl does not have to retype her query.

**Concern:**

If the search input is cleared when Kohl navigates back, she has to retype her query to continue searching — UX friction. If the results are not re-displayed, she loses context about what she was searching for.

**Property:**

Search state (query, results) persists across navigation to and from the editor.

**Implies:**
- navigation-preserves-search-input
- navigation-preserves-results-cache
- back-button-returns-to-search-state
