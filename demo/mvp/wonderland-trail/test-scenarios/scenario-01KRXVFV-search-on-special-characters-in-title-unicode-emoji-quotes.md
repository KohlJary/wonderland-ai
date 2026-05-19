## Scenario 083: Search on special characters in title: unicode, emoji, quotes

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9Q
**Severity:** curiosity

**Setup:**

Notes with titles: 'Hello "World"', 'Café', 'Note with emoji 🎉', "It's a test"

**Trigger:**

GET /api/search?query=quote (or café, or emoji, etc.)

**Expected:**

Text search handles unicode and special characters correctly

**Concern:**

The substring search might fail on unicode boundaries, or SQL might not handle emoji in LIKE clauses.

**Property:**

For all valid unicode strings U in a note's content, search(U) returns the note.
