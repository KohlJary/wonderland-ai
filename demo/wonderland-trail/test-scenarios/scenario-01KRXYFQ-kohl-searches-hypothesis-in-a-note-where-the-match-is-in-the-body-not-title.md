## Scenario 228: Kohl searches 'hypothesis' in a note where the match is in the body, not title

**GUID:** 01KRXYFQH721FMRYBB1WJJ1A0E
**Severity:** silent-wrongness

**Setup:**

Kohl has created a note with title 'Lab Notes' and body 'Testing the hypothesis on sample three.' She opens search.

**Trigger:**

Kohl types 'hypothesis' into the search input.

**Expected:**

The search results show the note 'Lab Notes' because the body contains 'hypothesis'. The body preview includes the word 'hypothesis' so Kohl can see why it matched.

**Concern:**

If body search is not implemented or is skipped, Kohl will miss notes that match her query only in the body. This reduces discoverability.

**Property:**

Substring search on body is case-insensitive and returns notes where body contains the query.
