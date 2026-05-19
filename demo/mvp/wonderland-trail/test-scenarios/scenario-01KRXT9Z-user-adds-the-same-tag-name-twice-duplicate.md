## Scenario 026: User adds the same tag name twice (duplicate)

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF2
**Severity:** degradation

**Setup:**

TagInput with one chip labeled 'testing' already present.

**Trigger:**

User types 'testing' again and presses Enter.

**Expected:**

The second 'testing' is rejected (no duplicate chip is added). Input is cleared. No error message shown to user. The component's internal state remains tag_names: ['testing'] (single entry).

**Concern:**

Component might add both instances, creating two 'testing' chips. When saved, the backend might deduplicate (or error). Better to prevent the duplicate on client-side so the user sees the tag is already there.

**Property:**

For all tags T in the current chip list, attempting to add T again must be rejected (case-sensitive for now, v1 scope).
