## Scenario 025: User attempts to add a tag name exceeding 100 characters

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF1
**Severity:** degradation

**Setup:**

TagInput with input focused.

**Trigger:**

User pastes a 150-character string (lorem ipsum text) and presses Enter.

**Expected:**

Tag is rejected client-side. Input is not cleared (so user can edit or delete). No chip is added. No error message is shown yet (but could be in future UX iteration).

**Concern:**

Component might allow the oversized tag to be added, and then the backend POST /notes fails with 400 'tag name exceeds 100 characters', which is worse UX (user loses their note edit state during save).

**Property:**

For all tag names T with len(T) > 100, the component must reject T before adding it to the chip list.
