## Scenario 029: Save fails with 400 validation error; tags should be preserved

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF5
**Severity:** degradation

**Setup:**

Editor with tags: ['rust', 'python']. User has a long body that exceeds the server's limit. User clicks Save.

**Trigger:**

Backend returns 400: {error: 'body exceeds max length'}. Frontend receives error response.

**Expected:**

Error is displayed to user. The tag list is preserved (NOT cleared). User can fix the body and click Save again without re-entering the tags.

**Concern:**

Component might clear the tag list on any POST /notes attempt (even failed ones), forcing user to re-enter tags. This is bad UX for a multi-field form where one field might fail validation.

**Property:**

Tag state must only be cleared on successful save (2xx response), never on error responses (4xx, 5xx, or network failure).
