## Scenario 093: Kohl searches for a single-word query and the substring match works (not requiring word boundary)

**GUID:** 01KRXVGHT2Y73C5JV7SEK1JJ7B
**Severity:** silent-wrongness

**Setup:**

Kohl has notes titled 'Understanding async' and 'Async Rust patterns'. She searches for 'async' and expects both to be returned.

**Trigger:**

Kohl types 'async' in the search box and submits.

**Expected:**

Both notes are returned in the results. The search is a case-insensitive substring match, not a whole-word match. If she searches for 'syn', both notes are also returned.

**Concern:**

If the search uses word-boundary matching (FTS5 phrase queries), she won't find 'async' when searching for 'syn'. She'll think the note doesn't exist. Substring matching is more forgiving and aligns with user expectations for a simple search box.

**Property:**

Substring matching works for both full words and word fragments
