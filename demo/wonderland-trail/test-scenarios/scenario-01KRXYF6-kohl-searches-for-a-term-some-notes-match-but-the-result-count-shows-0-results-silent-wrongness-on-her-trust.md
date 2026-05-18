## Scenario 225: Kohl searches for a term, some notes match but the result count shows '0 results' — silent wrongness on her trust

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HXE
**Severity:** breakage

**Setup:**

Kohl has notes containing 'hypothesis'. She searches for 'hypothesis'.

**Trigger:**

The backend search endpoint (or frontend filtering) fails to find the notes correctly.

**Expected:**

The result count displays the correct number of matching notes (>0). Each matching note is listed in the results pane.

**Concern:**

If the search result count is wrong, Kohl loses trust in search. She might manually scroll through her notes instead of using the feature. This is a silent-wrongness failure: the UI appears to function (no error toast), but the results are factually incorrect.

**Property:**

Search accuracy is non-negotiable; wrong result counts are silent failures that erode feature usability.

**Implies:**
- search-query-accuracy
- result-count-verification
- no-silent-filtering-errors
