## Scenario 191: Kohl searches for a phrase with special regex chars and gets results, not errors

**GUID:** 01KRXYDGJMBMVN3X0NM5ETQ1NT
**Severity:** silent-wrongness

**Setup:**

Kohl has a note with body 'C++ is fast. (Really!) [citation needed]'. She is on the search page.

**Trigger:**

Kohl types 'C++' into the search box and submits the query.

**Expected:**

The search returns 1 result (the note with 'C++' in the body). The result displays the note's title and a 150-char preview of the body that includes the matched text 'C++'.

**Concern:**

If the search backend treats '+', '(', ')', '[', ']' as regex special characters without escaping, the query fails with a 500 error or returns 0 results (wrong). Kohl typed a plain text search; she should get plain text matching.

**Property:**

search-query-special-char-handling-must-not-crash-or-silently-fail
