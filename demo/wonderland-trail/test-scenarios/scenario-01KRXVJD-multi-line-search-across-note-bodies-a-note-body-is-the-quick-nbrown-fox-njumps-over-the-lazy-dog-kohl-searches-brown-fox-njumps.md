## Scenario 105: Multi-line search across note bodies: A note body is 'The quick\nbrown fox\njumps over the lazy dog'. Kohl searches 'brown fox\njumps'.

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY4B
**Severity:** degradation

**Setup:**

A note has a multi-line body with line breaks.

**Trigger:**

Kohl searches for a phrase that spans a line break in the note body.

**Expected:**

If the phrase appears in the body (even across lines), the note is found.

**Concern:**

JavaScript substring matching works across line breaks, but only if the search term includes the newline. If Kohl searches 'brown fox' (with space, not newline), it won't find 'brown\nfox' (with newline). This is correct substring matching behavior, but Kohl might expect 'brown fox' to match 'brown\nfox'.

**Property:**

Search is literal substring matching; newlines in the note must match newlines in the search term.
