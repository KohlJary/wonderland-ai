## Scenario 090: Kohl searches with special characters in her query and doesn't trigger a crash or SQL error

**GUID:** 01KRXVGHT2Y73C5JV7SEK1JJ78
**Severity:** silent-wrongness

**Setup:**

Kohl has a note titled 'What's the deal with `null`?' She tries to search for it using the exact title.

**Trigger:**

Kohl types 'What's the deal with `null`?' into the search box and submits.

**Expected:**

The search endpoint handles the single quote, backticks, and question mark safely. It returns the matching note without error. If the special characters have special meaning in SQLite's FTS5 syntax (e.g., backticks are operators), the backend sanitizes or escapes them so they're treated as literal characters.

**Concern:**

If special characters cause a SQL syntax error, the search crashes or returns a 500. If they're silently stripped, Kohl's search query is misinterpreted and she won't find the note. Both are failures, but silent misinterpretation is worse—she'll think the note doesn't exist.

**Property:**

FTS5 query is sanitized to prevent syntax errors and preserve literal search intent
