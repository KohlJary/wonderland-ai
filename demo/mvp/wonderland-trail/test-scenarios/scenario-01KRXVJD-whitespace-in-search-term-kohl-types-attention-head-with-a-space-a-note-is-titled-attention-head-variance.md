## Scenario 102: Whitespace in search term: Kohl types 'attention head' (with a space); a note is titled 'attention-head variance'

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY48
**Severity:** degradation

**Setup:**

App has a note titled 'attention-head variance'.

**Trigger:**

Kohl types 'attention head' (with space).

**Expected:**

The note appears in results if the body contains 'attention head' (with space). It may not match the title (which has a hyphen, not a space).

**Concern:**

Does the search match 'attention head' as a substring in 'attention-head'? No. So Kohl's search doesn't find the note. But if Kohl searches 'attention-head' (with hyphen), it finds the title. The search is literal substring matching, so this is correct behavior. But Kohl might be confused.

**Property:**

Search is literal substring matching; spaces in the search term must match spaces in the note (not hyphens or other whitespace variants).
