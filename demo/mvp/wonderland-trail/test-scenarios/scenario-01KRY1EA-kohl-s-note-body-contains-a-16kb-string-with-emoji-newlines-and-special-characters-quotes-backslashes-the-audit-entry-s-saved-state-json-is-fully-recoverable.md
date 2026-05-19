## Scenario 357: Kohl's note body contains a 16KB string with emoji, newlines, and special characters (quotes, backslashes); the audit entry's saved_state JSON is fully recoverable

**GUID:** 01KRY1EAP8DPXCMJPQSNAEYA5W
**Severity:** silent-wrongness

**Setup:**

Kohl's draft body is 'Research findings 🔬 from Q1 2026:\n- Item 1: He said \"hello\"\n- Item 2: 日本語 test\n' (repeated to ~16KB). Note title is 'Q1 Research', tags are ['research', '日本語', 'emoji-test'].

**Trigger:**

Kohl clicks Save.

**Expected:**

HTTP 200 response is received. An audit_log entry is created. The saved_state JSON field contains the full body string (not truncated), with all emoji, newlines, and special chars preserved. JSON structure is valid (no unescaped quotes breaking the JSON). A subsequent SELECT FROM audit_log and JSON parsing the saved_state field recovers the exact body string Kohl saved.

**Concern:**

If emoji or non-ASCII characters are mangled during JSON serialization, the reconstructed state is corrupted. If quotes or backslashes are not escaped, the JSON is invalid and parsing fails. If the body is truncated at a code-point boundary (mid-emoji), the string is malformed.

**Property:**

saved_state JSON is valid UTF-8 JSON; all special characters (emoji, non-ASCII, quotes, backslashes) are correctly escaped; saved_state can be round-tripped (JSON parse → original string → JSON serialize → parse again produces identical result)

**Implies:**
- Backend must use a JSON library that correctly escapes special characters
- Test parsing the JSON after write to verify round-trip correctness
