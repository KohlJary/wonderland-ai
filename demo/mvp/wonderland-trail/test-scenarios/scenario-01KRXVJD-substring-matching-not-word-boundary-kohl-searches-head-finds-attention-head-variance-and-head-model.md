## Scenario 097: Substring matching (not word-boundary): Kohl searches 'head', finds 'attention-head variance' and 'head model'

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY43
**Severity:** breakage

**Setup:**

App has notes with 'attention-head variance' in title and 'head model' in body.

**Trigger:**

Kohl types 'head'.

**Expected:**

Both notes appear in results. The story says 'substring-matching'.

**Concern:**

If search requires word boundaries, 'attention-head' might not match 'head' (depending on how boundaries are defined). Kohl expects 'head' to find 'attention-head variance', per the acceptance criteria.

**Property:**

For all search terms T, a note N appears in results if T appears as a substring in title(N) or body(N), regardless of word boundaries.
