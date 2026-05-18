## Scenario 086: Kohl searches for 'rust' and finds three experimental notes tagged with it

**GUID:** 01KRXVGHT2Y73C5JV7SEK1JJ74
**Severity:** silent-wrongness

**Setup:**

Kohl has three notes: 'Rust ownership experiment', 'Memory safety vs. Go', 'Rust async patterns deep dive'. All three are tagged 'rust'. She opens the search form.

**Trigger:**

Kohl types 'rust' in the search box and the page debounces and submits the query.

**Expected:**

Results show all three notes in reverse chronological order (newest first). Each result shows title, a 150-char preview of the body, tags, and created_at. Pagination shows page 1 of 1 (3 total results). Kohl can read each title and snippet without scrolling.

**Concern:**

If search doesn't return all matching notes or returns them in the wrong order, Kohl thinks she's lost work she knows exists. Silent wrongness is worse than no results—she'll keep searching, wasting time.

**Property:**

Full-text search on title finds all substring matches
