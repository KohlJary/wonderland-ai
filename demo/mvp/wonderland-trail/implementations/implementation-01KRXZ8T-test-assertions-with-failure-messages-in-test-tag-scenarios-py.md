## Implementation 051: Test assertions with failure messages in test_tag_scenarios.py

**GUID:** 01KRXZ8TWGFEGRZFWVZZ3BNVV9
**Side:** frontend
**Ticket:** 057
**Contract:** no contract change — this is test-only mechanical work
**Ready for review:** yes

**Approach:**

Scanned test_tag_scenarios.py for assertions lacking failure messages, added descriptive f-string messages that name the expected value, actual value, and context. Matched the style and detail level already present in test_notes_edge_cases.py. No logic changes — purely improving debuggability.

**Client State:**

n/a — test file, no client state

**Files:**
- tests/test_tag_scenarios.py: added failure messages to ~10 assertions across 4 test functions
