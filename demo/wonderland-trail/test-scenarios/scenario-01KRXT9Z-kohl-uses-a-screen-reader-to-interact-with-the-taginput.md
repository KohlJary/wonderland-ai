## Scenario 034: Kohl uses a screen reader to interact with the TagInput

**GUID:** 01KRXT9ZVW04FW51CD98MPDCFA
**Severity:** degradation

**Setup:**

TagInput component rendered in the editor. Accessibility attributes (aria-label, aria-live, role) are in place.

**Trigger:**

Screen reader user navigates to the input field and adds a tag.

**Expected:**

Screen reader announces the input field's purpose ('Tag input' or similar). When a tag is added, the updated chip list is announced ('tag added: rust').

**Concern:**

Component might lack aria-labels or aria-live regions, making it unusable for screen reader users.

**Property:**

The component must include appropriate ARIA attributes so screen reader users can understand its purpose and be notified when tags are added or removed.
