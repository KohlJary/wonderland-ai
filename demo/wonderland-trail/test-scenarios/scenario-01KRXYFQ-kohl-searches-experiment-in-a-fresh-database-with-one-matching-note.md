## Scenario 227: Kohl searches 'experiment' in a fresh database with one matching note

**GUID:** 01KRXYFQH721FMRYBB1WJJ1A0D
**Severity:** silent-wrongness

**Setup:**

Kohl has created one note with title 'First Experiment' and body 'Testing the hypothesis.' She opens the search view.

**Trigger:**

Kohl types 'experiment' into the search input.

**Expected:**

The search results show exactly one note: 'First Experiment'. The body preview displays 'Testing the hypothesis.' Kohl can see the match is in the title.

**Concern:**

If substring matching is broken or case-insensitive matching fails, Kohl won't find notes she knows she wrote. This is a core feature.

**Property:**

Substring search on title is case-insensitive and returns exact matches.
