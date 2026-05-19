## Scenario 221: Kohl types a search term, then deletes it all, leaving an empty input — search clears results without crashing

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HXA
**Severity:** silent-wrongness

**Setup:**

Kohl has typed 'findings' and sees 2 results. She then selects all the text and deletes it, leaving an empty input field.

**Trigger:**

The search input becomes empty (zero characters or only whitespace).

**Expected:**

The search results pane clears or displays a message like 'Enter a search term to find notes.' No error toast appears. The search does not fire a query to the backend (to avoid unnecessary load). Kohl can immediately type a new search term and see results.

**Concern:**

If an empty-query request fires to the backend, it wastes bandwidth and might return all notes (unexpected). If the UI crashes or shows an error, Kohl thinks the feature is broken. If results linger, Kohl is confused about what she's seeing.

**Property:**

Empty or whitespace-only queries are non-operations; they don't fetch or display results.

**Implies:**
- empty-query-validation
- no-backend-request-on-empty
- results-cleared-on-empty
