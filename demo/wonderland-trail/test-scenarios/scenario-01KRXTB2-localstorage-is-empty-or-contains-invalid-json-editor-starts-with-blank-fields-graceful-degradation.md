## Scenario 047: localStorage is empty or contains invalid JSON; editor starts with blank fields (graceful degradation)

**GUID:** 01KRXTB2N1T8SKB4XW9T1D9EW5
**Severity:** degradation

**Setup:**

localStorage['noteDraft'] is either undefined, null, an empty string, or contains corrupted/malformed JSON.

**Trigger:**

EditorPane mounts.

**Expected:**

The component does not crash. The title and body fields start blank. No error is thrown to the user.

**Concern:**

If the restore logic assumes localStorage['noteDraft'] is always valid JSON, a corrupted entry will throw JSON.parse error and crash the component or leave it in an error state.

**Property:**

For all states of localStorage (empty, null, invalid JSON), the component mounts without crashing and displays blank input fields.
