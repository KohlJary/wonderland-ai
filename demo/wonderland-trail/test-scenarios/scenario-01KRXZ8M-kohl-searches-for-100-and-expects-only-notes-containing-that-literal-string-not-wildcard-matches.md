## Scenario 238: Kohl searches for '100%' and expects only notes containing that literal string, not wildcard matches

**GUID:** 01KRXZ8M0J7CVP08DRGHREWYNT
**Severity:** silent-wrongness

**Setup:**

Three notes exist in the database: (1) 'CPU at 100% usage', (2) '100 percent complete', (3) 'CPU load'. Kohl types '100%' into the search box.

**Trigger:**

Kohl submits the search query '100%' via GET /api/search?q=100%.

**Expected:**

Search returns only note (1) 'CPU at 100% usage' — the one containing the literal string '100%'. Notes (2) and (3) do not match because they lack the literal '%' character. The % is treated as a literal character, not a LIKE wildcard.

**Concern:**

If the search implementation does not escape the % character in the user input before passing it to SQLite LIKE, the % will match zero or more characters, causing notes (2) and (3) to incorrectly appear in results. Kohl sees more results than expected and cannot tell why her search is too broad. This is silent wrongness — the system appears to work, but returns the wrong data.

**Property:**

User-input wildcard metacharacters must be escaped before being used in LIKE patterns, and the escape parameter must be passed to ilike().

**Implies:**
- test_escape_like_pattern_escapes_percent_to_literal
- test_escape_like_pattern_escapes_underscore_to_literal
- test_search_endpoint_uses_escaped_pattern_with_escape_parameter
- test_search_with_multiple_wildcards_in_input
