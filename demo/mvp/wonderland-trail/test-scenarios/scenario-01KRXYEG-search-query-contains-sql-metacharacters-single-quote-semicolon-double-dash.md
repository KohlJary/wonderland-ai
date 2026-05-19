## Scenario 212: Search query contains SQL metacharacters: single quote, semicolon, double dash

**GUID:** 01KRXYEG9WMJ0GPZ2FAHJSYB4W
**Severity:** silent-wrongness

**Setup:**

Note with title 'O'Reilly'. User searches for O'Reilly. Database backend uses SQLite.

**Trigger:**

GET /api/notes/search?q=O'Reilly

**Expected:**

Endpoint returns the note with title containing O'Reilly, no SQL error.

**Concern:**

If query is concatenated directly into a SQL WHERE clause without parameterization ('SELECT * FROM notes WHERE title LIKE '%' + q + '%''), the single quote will break the query string and either cause a SQL syntax error or, worse, enable SQL injection. Silent wrongness if the error is swallowed and empty results are returned.

**Property:**

For all query strings Q that contain SQL metacharacters (' ; -- /* */ etc.), the endpoint must return correct results or fail loudly with 400, never produce unexpected results.

**Implies:**
- Implies code-quality check — flag for Caterpillar on review: verify parameterized queries or escaping is in place.
