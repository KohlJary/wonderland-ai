## Scenario 230: Kohl searches for a partial word (substring, not whole word)

**GUID:** 01KRXYFQH721FMRYBB1WJJ1A0G
**Severity:** silent-wrongness

**Setup:**

Kohl has a note with body 'The hypothesis was tested.' She opens search.

**Trigger:**

Kohl types 'hypoth' (first 6 characters of 'hypothesis').

**Expected:**

The note is found because substring search matches 'hypoth' within 'hypothesis'.

**Concern:**

If substring matching requires whole words or exact matches, Kohl can't use prefixes to find notes, and search becomes much less useful.

**Property:**

Substring search matches any contiguous characters, not whole words only.
