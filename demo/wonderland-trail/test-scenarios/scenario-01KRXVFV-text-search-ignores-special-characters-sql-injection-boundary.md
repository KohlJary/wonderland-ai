## Scenario 073: Text search ignores special characters / SQL injection boundary

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9D
**Severity:** silent-wrongness

**Setup:**

Note with title='100% done!', body='Cost: $1,000'

**Trigger:**

GET /api/search?query=% (percent sign, which is LIKE wildcard)

**Expected:**

Either returns the note (matches literal %) or returns empty (% is treated as literal), but doesn't crash or misinterpret the query

**Concern:**

If the code builds a LIKE query naively, the % will be treated as wildcard. User searches for '%' (literal), the code executes LIKE '%' (match everything), and the user gets wrong results. Even worse if the code is vulnerable to SQL injection via query parameter.

**Property:**

For all special characters in SQL (%, _, ', "), searching for the character literally returns notes containing that literal character (or is properly escaped).

**Implies:**
- Implies security implications if query parameter is not properly parameterized — flag for Queen.
- Suggests implementation should use parameterized queries or proper escaping of LIKE special characters.
