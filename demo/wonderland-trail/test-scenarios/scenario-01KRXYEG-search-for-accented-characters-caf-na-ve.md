## Scenario 214: Search for accented characters: café, naïve, ñ

**GUID:** 01KRXYEG9WMJ0GPZ2FAHJSYB4Y
**Severity:** degradation

**Setup:**

Note with title 'Café notes' in UTF-8. User searches for 'cafe' (no accent).

**Trigger:**

GET /api/notes/search?q=cafe

**Expected:**

Endpoint returns the note with title 'Café notes' (case-insensitive accent-insensitive match), OR returns no match but documents that accent-folding is not supported in v1.

**Concern:**

Substring search with case-insensitivity is stated, but accent-insensitivity is not. If the backend does byte-level case-insensitive search, 'cafe' will not match 'Café' because UTF-8 encoding of é differs from e. Silent wrongness if users expect accent-insensitive matching and it silently fails.

**Property:**

For all Unicode strings in notes and query Q, search must either match accent-insensitively or clearly document that it does not.
