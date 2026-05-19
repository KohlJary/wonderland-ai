## Scenario 203: Search query with special characters in markdown (*, _, `) is highlighted correctly

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHH
**Severity:** silent-wrongness

**Setup:**

Kohl has a note with body: '**bold text** and _italic_ and `code snippet`'. She searches for '**bold'.

**Trigger:**

Search input receives '**bold'. Client sends request. Results return with highlighting.

**Expected:**

The text '**bold' is highlighted in the results preview (or at least the note is returned as a match).

**Concern:**

If the frontend applies DOMPurify or markdown rendering to the search result excerpt *before* applying highlighting, the ** is converted to HTML tags and the literal string '**bold' no longer exists in the DOM. Highlighting fails. Alternatively, if highlighting is applied before sanitization, the highlight markup itself might be stripped as unsafe HTML.

**Property:**

For all search queries matching markdown syntax characters, the note is returned as a match and highlighting is applied consistently (either before or after sanitization, but not both, causing misalignment).

**Implies:**
- Implies rendering concern: Clarify the order of operations: (1) get raw body, (2) apply search highlighting, (3) render markdown, sanitize. OR (1) render markdown, sanitize, (2) apply highlighting to the rendered HTML. The choice affects whether markdown syntax characters survive highlighting.
