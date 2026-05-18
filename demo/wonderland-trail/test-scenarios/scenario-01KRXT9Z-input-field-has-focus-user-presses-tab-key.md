## Scenario 033: Input field has focus; user presses Tab key

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF9
**Severity:** curiosity

**Setup:**

TagInput with focus on the input field. Input contains 'draft'.

**Trigger:**

User presses Tab key (without pressing Enter first).

**Expected:**

Focus moves to the next focusable element (likely the Save button or next form field). The 'draft' tag is not added (Enter was not pressed). Input retains the text 'draft'.

**Concern:**

Component might interpret Tab as an intent to add the tag (like Enter), or might clear the input on blur, causing the user to lose their draft text.

**Property:**

Only Enter key or explicit Add button click should trigger tag addition. Tab (and other keys like Shift, Ctrl) should not trigger addition.
