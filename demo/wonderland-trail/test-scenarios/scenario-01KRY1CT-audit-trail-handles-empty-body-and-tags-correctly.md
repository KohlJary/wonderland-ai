## Scenario 327: Audit trail handles empty body and tags correctly

**GUID:** 01KRY1CT9RYR088A6WTPTNAHT9
**Severity:** degradation

**Setup:**

Kohl creates a note with title "stub" and an empty body. She saves it with no tags. The backend writes note with body = "" and tags = []. The audit_log entry is written with saved_state.

**Trigger:**

The save completes and returns 200.

**Expected:**

The audit_log entry has saved_state JSON with body: "" (empty string, not NULL) and tag_ids: [] (empty array, not NULL or omitted). Both fields are present and correctly represent the empty state.

**Concern:**

The audit trail might represent empty state incorrectly: body stored as NULL instead of "", tag_ids omitted entirely. JSON serialization might not handle empty arrays/strings correctly, leading to parse errors on later reads.

**Property:**

For every saved note, the audit_log entry's saved_state includes all fields with correct types: title (string), body (string, possibly empty), tag_ids (array, possibly empty), tag_names (array, possibly empty), timestamps. No fields are NULL or omitted.

**Implies:**
- JSON serialization must handle all edge cases (empty strings, empty arrays, NULL vs missing)
- The schema must clearly define what 'full state' includes
- Test data should include edge cases: no tags, empty body, title only
