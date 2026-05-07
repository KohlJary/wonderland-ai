## Test Scenario 001: XSS Injection via Script Tags in Markdown

**Severity:** breakage

**Setup:**

User alice is authenticated and has a valid session. Backend has POST /homepage/:slug endpoint accepting {content: markdown_string} per contract-003. The markdown parser is wired to the response flow.

**Trigger:**

User POSTs {content: '<script>alert("xss")</script>'} to POST /homepage/alice.

**Expected:**

Backend sanitizes the script tag. Response 200 includes {status: 'published', content_html: '...'} where content_html contains no `<script>` tag and no executable code. When the published homepage is retrieved via GET /homepage/alice, the response HTML contains no `<script>` tag. Visiting the page in a browser does not trigger any alert.

**Concern:**

XSS injection is one of the oldest web attack vectors and one of the most dangerous. Without sanitization, users visiting alice's homepage could have cookies stolen (session hijacking), personal data exfiltrated, or malware injected. This is a silent-wrongness scenario: the publish appears to succeed, the page appears to render, but it contains invisible malice that executes when visitors arrive. Story-002 requires 'XSS is not possible'; contract-003 specifies sanitization via remark-sanitize. This test verifies the boundary is enforced.

**Property:**

For all markdown M with embedded `<script>` tags, the sanitized output must not execute any JavaScript when rendered in a browser.

**Implies:**

- Requires markdown parser with XSS sanitization (remark-sanitize or equivalent)
- Requires test of multiple XSS vectors (not just script tags; see test_markdown_and_xss.py for onclick, data: URIs, etc.)
- Implies story-002 confusion-flag about 'XSS is not possible' is addressed by architecture
