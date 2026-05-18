## Scenario 217: Search for phrase vs. word: user searches 'hello world' as one query

**GUID:** 01KRXYEG9WMJ0GPZ2FAHJSYB51
**Severity:** curiosity

**Setup:**

Notes: 'hello there', 'world peace', 'hello world today'. User searches for 'hello world'.

**Trigger:**

GET /api/notes/search?q=hello%20world

**Expected:**

Unclear from ticket. Does this match: (a) notes containing 'hello' AND 'world' anywhere, (b) notes containing 'hello world' as a substring, (c) notes containing 'hello' OR 'world'?

**Concern:**

Ticket says 'basic full-text matching (case-insensitive substring search)' which suggests substring ('hello world' as a literal phrase), but 'full-text' sometimes implies term-based matching (AND/OR logic). Acceptance doesn't clarify. Silent wrongness if frontend expects one behavior and backend implements another.

**Property:**

For all multi-word queries Q, the endpoint behavior must be explicitly specified: phrase search, AND, OR, or other.
