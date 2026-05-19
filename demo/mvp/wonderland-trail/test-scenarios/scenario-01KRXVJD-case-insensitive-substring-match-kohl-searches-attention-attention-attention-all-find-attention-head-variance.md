## Scenario 096: Case-insensitive substring match: Kohl searches 'ATTENTION', 'Attention', 'attention' — all find 'attention-head variance'

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY42
**Severity:** breakage

**Setup:**

App has a note titled 'attention-head variance'.

**Trigger:**

Kohl types 'ATTENTION' (all caps) or 'Attention' (title case) or 'attention' (lowercase).

**Expected:**

All three variants find the 'attention-head variance' note. The story says 'case-insensitive'.

**Concern:**

If search is case-sensitive, only 'attention' (exact case) finds it. Kohl's search intention is frustrated.

**Property:**

For all search terms T and all notes N, N appears in results if title(N) or body(N) contains T (case-insensitive, substring).
