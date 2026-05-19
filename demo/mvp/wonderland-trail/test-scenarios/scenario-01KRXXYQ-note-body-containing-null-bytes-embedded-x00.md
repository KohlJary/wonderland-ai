## Scenario 170: Note body containing null bytes (embedded \x00)

**GUID:** 01KRXXYQD08R1GFPSWEN113273
**Severity:** curiosity

**Setup:**

Request with body='Hello\x00World' (null byte embedded).

**Trigger:**

POST /api/notes with the above body.

**Expected:**

Body is stored and retrieved as-is (if valid UTF-8), or null bytes are rejected/stripped.

**Concern:**

Null bytes (U+0000) are valid in UTF-8. Python strings can hold them. JSON serialization might fail, or null bytes might be stripped. Worth checking.

**Property:**

Note body round-trips correctly through the API, including all valid UTF-8.
