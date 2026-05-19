## Scenario 202: Search query with regex metacharacters is escaped before highlighting

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHG
**Severity:** silent-wrongness

**Setup:**

Kohl has a note with body: 'Cost function: C(x) = x^2'. She searches for the query 'C(x)'.

**Trigger:**

Search input receives 'C(x)'. Client sends request to /api/search?q=C(x). Results are returned with highlights applied.

**Expected:**

The text 'C(x)' in the note body is highlighted without error. The search result shows the note with the match highlighted cleanly.

**Concern:**

If the frontend naively applies the query string to a regex (e.g., /C(x)/g), the parentheses are interpreted as a regex group capture, not literal characters. The regex fails silently or throws an error. Kohl sees no results or a broken highlight, and believes her note doesn't exist.

**Property:**

For all search queries Q containing regex metacharacters (., *, +, ?, [, ], {, }, (, ), ^, $, |, \), highlighting is safe and produces visually correct output without throwing or silently failing.

**Implies:**
- Implies engineering concern: Use String.replace() with regex escape (e.g., lodash.escapeRegExp) or simpler substring-based highlighting (indexOf + slice) rather than naive regex. Flag for Tweedledee to choose the safe approach.
