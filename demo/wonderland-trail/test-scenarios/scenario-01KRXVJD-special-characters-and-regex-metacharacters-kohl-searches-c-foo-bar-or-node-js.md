## Scenario 100: Special characters and regex metacharacters: Kohl searches 'C++', 'foo*bar', or 'node.js'

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY46
**Severity:** silent-wrongness

**Setup:**

App has notes titled 'C++ Basics', 'foo*bar pattern', 'node.js tutorial'.

**Trigger:**

Kohl types 'C++' or 'foo*bar' or 'node.js'.

**Expected:**

The matching notes appear.

**Concern:**

If search uses regex without escaping, 'C++' becomes a regex (C followed by one or more '+'), 'foo*bar' becomes a regex (fo with zero or more 'o's), 'node.js' becomes a regex (node or nodej or s). Kohl gets wrong results.

**Property:**

Search is literal substring matching, not regex. Special characters are treated as literal characters.
