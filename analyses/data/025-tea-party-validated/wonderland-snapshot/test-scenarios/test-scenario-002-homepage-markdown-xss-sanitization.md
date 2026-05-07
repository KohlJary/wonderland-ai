## Scenario: Homepage edit — XSS injection via malformed Markdown

**Severity:** silent-wrongness (most dangerous class)

**Setup:**

Priya is logged in and editing her homepage. She (innocently) pastes a code snippet that includes unescaped HTML. Or: an attacker has compromised a related service and is injecting XSS vectors via the markdown field.

Example input:
```
# My Page

<img src=x onerror="alert('pwned')">

Click [here](javascript:void(0))
```

**Trigger:**

POST /api/user/me/homepage with raw_markdown containing the above. Backend parses with commonmark and sanitizes HTML. Saves raw_markdown + rendered_html. On the next GET /user/priya, the rendered_html is returned to a visitor.

**Expected:**

1. The malicious event handlers are stripped. The rendered_html should contain no `onerror`, no `javascript:` URLs, no `<script>` tags.
2. The img tag itself may remain (as an img tag with src=x), or be stripped entirely—depends on the sanitization policy. Policy should be documented. We recommend: strip all dangerous attributes, allow safe tags (p, div, h1-h6, strong, em, a, code, pre, blockquote, ul, ol, li). NO style, NO event handlers.
3. The homepage renders without executing the injected code.

**Concern:**

The contract says "backend receives raw markdown, validates it's under size limit, parses with commonmark, sanitizes HTML, stores both raw + rendered." But sanitization is the easiest place to be sloppy. Common failure modes:

1. **No sanitization at all** — raw HTML is stored and rendered. Visitor's browser executes the malicious code.
2. **Sanitization only on read, not on write** — raw_markdown is stored unsanitized, rendered_html is sanitized. Visitor is safe, but if the sanitizer changes or the raw_markdown is later exported, XSS leaks.
3. **Blacklist sanitization** — code tries to strip only known-bad tags (e.g., `<script>`). Attacker finds an untested vector (e.g., SVG+script, or `<img srset>`).
4. **Incomplete HTML escaping** — code escapes HTML entities but doesn't handle HTML attributes in links or images.

We assume the team uses a whitelist-based HTML sanitizer (bleach, nh3, or similar) and applies it on write.

**Property:**

For all inputs I (markdown, including hostile inputs), and for all visitors V viewing the rendered homepage: I cannot cause V's browser to execute code or access V's localStorage, cookies, or sensitive DOM elements without V's explicit action.

More specifically: the output of HTML-parsing(I) with full HTML sanitization applied should contain zero XSS vectors per OWASP XSS guidelines. Any event handler attributes, javascript: URLs, iframe/script/embed/object tags, or data: URLs with executable content should be stripped.

**Implies:**

Implies security review (flag for Queen of Hearts). Implies choice of sanitizer library (Tweedledum's domain—backend implementation). Implies test coverage for a wide range of XSS vectors, not just `<script>`.

---

## Notes for Test Implementation

The pytest test will:
1. Create/update a homepage with malicious markdown.
2. Fetch the rendered homepage (as a visitor, unauthenticated).
3. Assert that dangerous attributes and URLs are not present in the rendered_html.
4. Verify that benign HTML (italics, links, images with safe src) is preserved.

This test will FAIL until the backend implements sanitization correctly.
