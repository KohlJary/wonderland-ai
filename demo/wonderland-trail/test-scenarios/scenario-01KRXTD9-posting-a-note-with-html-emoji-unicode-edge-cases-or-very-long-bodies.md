## Scenario 061: Posting a note with HTML, emoji, unicode edge cases or very long bodies

**GUID:** 01KRXTD96CAEAJCAJEH0RQWM05
**Severity:** curiosity

**Setup:**

POST /api/notes with body containing: <script>alert('xss')</script>, 😀😀😀 (1000 emoji), combining diacritics, or a 16384-character UTF-8 string.

**Trigger:**

POST with adversarial or edge-case body content.

**Expected:**

The note is created. The response preserves the body as-is (no sanitization by backend). Frontend is responsible for HTML-escaping before rendering.

**Concern:**

Pydantic enforces max_length on characters, not bytes. UTF-8 has variable-width encoding. A 16384-character string could be 50KB+ in bytes if it's all multi-byte characters. Emoji and combining diacritics can cause issues in some clients. Backend should handle without crashing or corrupting data.

**Property:**

For all UTF-8 strings S with len(S) <= 16384 characters, POST /api/notes with body=S succeeds and returns S as-is in the response.

**Implies:**
- Implies frontend concern: body content must be HTML-escaped before rendering to prevent XSS attacks.
- Implies tests: test_post_note_accepts_multiline_body, test_post_note_accepts_body_with_emoji.
