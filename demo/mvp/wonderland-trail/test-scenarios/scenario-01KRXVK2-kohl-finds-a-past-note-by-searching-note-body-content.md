## Scenario 107: Kohl finds a past note by searching note body content

**GUID:** 01KRXVK28H5RPDTG82TGG11W9Q
**Severity:** breakage

**Setup:**

Kohl has a note titled 'Session 1' with body containing 'The transformer architecture uses multi-head attention to compute token relationships.' She opens search.

**Trigger:**

Kohl types 'token relationships' into the search input and waits for debounce.

**Expected:**

The search results show the 'Session 1' note with the full title and a body preview that includes the matched phrase. The match is highlighted or clearly visible in the preview so Kohl can confirm this is the right note.

**Concern:**

If search doesn't find notes by body content, Kohl has to open every note to re-discover which one contains the detail she's looking for. This defeats the 'find past notes' user need entirely.

**Property:**

substring match on body
