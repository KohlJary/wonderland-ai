## Scenario 112: Kohl's search is case-insensitive

**GUID:** 01KRXVK28H5RPDTG82TGG11W9W
**Severity:** silent-wrongness

**Setup:**

Kohl has a note titled 'Attention Mechanisms'. She opens search.

**Trigger:**

Kohl types 'ATTENTION' (all caps) into the search input.

**Expected:**

The search result includes 'Attention Mechanisms' (title matched despite case difference). The match works for 'ATTENTION', 'attention', 'Attention', etc.

**Concern:**

If search is case-sensitive, Kohl has to remember the exact casing of her titles. She types 'attention' and misses 'Attention Mechanisms', thinking the note is missing. Case-insensitive search is a basic user expectation.

**Property:**

case-insensitive substring match
