## Scenario 091: Kohl searches with an empty query string and only the 'performance' tag filter, expecting tag-only results

**GUID:** 01KRXVGHT2Y73C5JV7SEK1JJ79
**Severity:** silent-wrongness

**Setup:**

Kohl selects the 'performance' tag filter but leaves the search text box empty. She wants to browse all notes with that tag without text filtering.

**Trigger:**

Kohl submits the search with empty query and tag='performance' selected.

**Expected:**

The endpoint returns all notes tagged 'performance' in reverse chronological order, paginated. The response includes all 'performance' notes, not an error or empty result.

**Concern:**

If the endpoint requires a non-empty query string, this fails with a 400 error. If it ignores the tag filter when query is empty, she gets all notes instead of filtered notes. Either way, her mental model of 'filter by tag' breaks.

**Property:**

Tag-only search (empty query string) is supported and returns all notes with the specified tag(s)
