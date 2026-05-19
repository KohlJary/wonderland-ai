## Scenario 113: Kohl's search results display accurate preview snippets

**GUID:** 01KRXVK28H5RPDTG82TGG11W9X
**Severity:** silent-wrongness

**Setup:**

Kohl has a note with a long body (500+ chars). She searches for a phrase that appears in the middle of the body (characters 200–220).

**Trigger:**

Kohl types the search term and views the results.

**Expected:**

The result's body preview shows the first 150 characters of the body (or a contextual snippet around the match, if smart snippeting is implemented). The preview is truncated cleanly (no dangling tags or incomplete words) and includes '...' at the end if truncated. Kohl can read enough to identify if this is the right note.

**Concern:**

If the preview is empty or shows only the first line, Kohl has to open the full note to verify it matches her search. This adds friction to discovery. If the preview is garbled (unclosed tags, half-rendered markdown), it's confusing.

**Property:**

body preview rendering
