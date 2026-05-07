## Test Scenario 003: Silent Wrongness — Markdown Parser Fails But Response Is 200

**Severity:** silent-wrongness

**Setup:**

Backend receives POST /homepage/:slug with valid JSON and a markdown string that the markdown parser rejects (parser raises an exception). Backend catches the exception but stores the raw markdown anyway and returns {status: 'published', ...} with 200 OK. User sees a success message.

**Trigger:**

User POSTs markdown with an edge case: deeply nested blockquotes (100+ levels), or unclosed code block, or some other malformed input that causes the remark parser to fail.

Example: `markdown = "> " * 200 + "quote"` (200 nested blockquotes, likely to cause parser failure or stack overflow).

**Expected:**

If parser fails, return 422 Unprocessable Entity with {error: 'markdown_parse_error', details: 'Parser encountered stack overflow at depth 150'}. Do NOT return 200. User sees an error message and can revise their content.

**Concern:**

This is the most dangerous class of failure: silent wrongness. The system appears to succeed (200 response, success message), but the content is corrupted or unrendered. User alice publishes what she thinks is valid markdown, gets a success message, shares the link with her collaborators. They visit the page and see mangled HTML or raw markdown rendering (depending on the failure mode). They think alice is incompetent or the platform is broken, but alice has no idea because the response was 200.

Contract-003 explicitly specifies: "Failure mode: if markdown parser fails (e.g., malformed input), store raw content and return 422 {error: 'markdown_parse_error', details: 'Parser encountered invalid syntax at line N'} (don't corrupt the write; let frontend decide whether to retry or ask user to revise)."

This test verifies that the error path is real and taken, not skipped.

**Property:**

For all markdown M that causes the parser to raise an exception, POST /homepage/:slug must return 4xx or 5xx, not 200. The response must include an error code and message.

**Implies:**

- Requires try/catch around markdown parser: catch parser exceptions and return 422, not 200.
- Requires test data that triggers parser failures (deep nesting, malformed syntax).
- Implies that raw markdown is never stored without rendering (unless explicitly designing a "store and fail" option).
- Implies the error response includes helpful message so user knows what went wrong.
