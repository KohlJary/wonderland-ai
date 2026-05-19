## Scenario 071: Case-insensitive substring match on title

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9B
**Severity:** breakage

**Setup:**

Note created: title='Research Journal', body='daily notes'

**Trigger:**

GET /api/search?query=research (lowercase, note title is mixed case)

**Expected:**

Note is returned in results

**Concern:**

SQLite LIKE by default is case-insensitive on ASCII, but substring searches sometimes aren't. The note might not match if the code uses LIKE wrong or uses == instead of LIKE.

**Property:**

For all case variants C of a string S in a note's title or body, search(lowercase(C)) returns the note.
