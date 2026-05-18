## Scenario 158: Tag name is an empty string; rendering an empty badge looks wrong

**GUID:** 01KRXXXVW570ZA3859XC573SKE
**Severity:** degradation

**Setup:**

Due to a backend bug, a note is tagged with ['work', '', 'urgent'] (an empty string in the tag_names array). The note appears in search results.

**Trigger:**

renderNoteResult() renders all three tag names, including the empty one, as badge elements.

**Expected:**

The empty tag is either filtered out before rendering, or rendered as a transparent/invisible badge with zero height (not taking up space). The 'work' and 'urgent' badges render normally.

**Concern:**

If an empty string is rendered as a badge, it would show as a blank pill with just padding/border, wasting space and looking broken. The contract should forbid empty tag names, but if the backend sends them, the frontend should handle gracefully.

**Property:**

For all tag_names in a note, if any name is an empty string, it is either filtered out or renders invisibly without consuming space.
