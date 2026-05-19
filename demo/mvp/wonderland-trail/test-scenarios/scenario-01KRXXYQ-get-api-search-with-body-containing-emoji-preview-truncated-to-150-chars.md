## Scenario 167: GET /api/search with body containing emoji, preview truncated to 150 chars

**GUID:** 01KRXXYQD08R1GFPSWEN113270
**Severity:** curiosity

**Setup:**

Note with body='Hello 👋 this is a very long message...' (200+ chars with emoji).

**Trigger:**

GET /api/search.

**Expected:**

body_preview is first 150 *characters* (not bytes). Valid UTF-8. Emoji count as single chars.

**Concern:**

The code does body[:150] which slices at Python string character boundaries. Python 3 strings are Unicode, so emoji are single characters. Slicing at character 150 is safe and produces valid UTF-8.

**Property:**

body_preview is always valid UTF-8 and at most 150 characters.
