## Scenario: Audit trail handles empty body and tags correctly

**Severity:** degradation

**Setup:**
Kohl creates a note with title "stub" and an empty body (no text). She saves it with no tags. The backend writes note with body = "" and tags = []. The audit_log entry is written with saved_state = {title: "stub", body: "", tag_ids: [], ...}.

**Trigger:**
The save completes and returns 200.

**Expected:**
The audit_log entry has:
- saved_state JSON with body: "" (empty string, not NULL or omitted)
- tag_ids: [] (empty array, not NULL or omitted)
- Both fields are present and correctly represent the empty state

**Concern:**
The audit trail might represent empty state incorrectly:
- body might be stored as NULL instead of "" (breaking the contract that body is always a string)
- tag_ids might be omitted from saved_state entirely (breaking forensic reconstruction—if you don't know the tags, you don't know the full state)
- The JSON serialization might not handle empty arrays or strings correctly, leading to parse errors on later reads

This is especially dangerous because empty state is legitimate (a note can have no content, no tags) and should be fully captured in the audit trail.

**Property:**
For every saved note, the audit_log entry's saved_state includes all fields with correct types: title (string), body (string, possibly empty), tag_ids (array, possibly empty), tag_names (array, possibly empty), timestamps. No fields are NULL or omitted. Empty collections are represented as []; empty strings as "".

**Implies:**
- JSON serialization must handle all edge cases (empty strings, empty arrays, NULL vs missing)
- The schema must clearly define what "full state" includes
- Test data should include edge cases: no tags, empty body, title only, all empty except ID
