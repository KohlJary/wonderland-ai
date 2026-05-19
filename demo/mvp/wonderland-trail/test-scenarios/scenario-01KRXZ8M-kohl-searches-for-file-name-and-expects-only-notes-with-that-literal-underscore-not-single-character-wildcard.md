## Scenario 239: Kohl searches for 'file_name' and expects only notes with that literal underscore, not single-character wildcard

**GUID:** 01KRXZ8M0J7CVP08DRGHREWYNV
**Severity:** silent-wrongness

**Setup:**

Three notes exist: (1) 'file_name.txt', (2) 'filexname', (3) 'file name'. Kohl searches for 'file_name'.

**Trigger:**

Kohl submits the search query 'file_name' via GET /api/search?q=file_name.

**Expected:**

Search returns only note (1) 'file_name.txt' — the one containing the literal string 'file_name' with an underscore. Notes (2) and (3) do not match. The underscore is treated as a literal character, not a LIKE single-character wildcard.

**Concern:**

If the search implementation does not escape the _ character, it will match any single character (x in 'filexname', space in 'file name'), causing false positives. Kohl sees unexpected results and cannot understand why.

**Property:**

Underscore metacharacter must be escaped in user input before being used in LIKE patterns.

**Implies:**
- test_escape_like_pattern_escapes_underscore_to_literal
- test_search_with_underscore_in_query_matches_literal_only
