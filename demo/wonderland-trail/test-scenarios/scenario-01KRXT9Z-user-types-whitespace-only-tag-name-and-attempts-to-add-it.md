## Scenario 024: User types whitespace-only tag name and attempts to add it

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF0
**Severity:** degradation

**Setup:**

TagInput with input focused.

**Trigger:**

User types '   ' (three spaces) and presses Enter.

**Expected:**

Tag is trimmed to empty string; the add action is rejected (no tag appears, input remains '   '). User sees no feedback yet, but the tag is not added. (Client-side validation per acceptance criterion 'Tag names are trimmed and non-empty.')

**Concern:**

Component might add an empty string as a tag, creating a blank chip or later a server validation error when the note is saved. Silent failure on whitespace is better than adding junk.

**Property:**

For all inputs I, trim(I) must be non-empty before a tag is added. Whitespace-only inputs must be rejected client-side.
