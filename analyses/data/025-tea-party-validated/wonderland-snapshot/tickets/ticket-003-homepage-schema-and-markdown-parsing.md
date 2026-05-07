## Ticket 003: Homepage schema and markdown parsing

**Sources:** edit-my-homepage-in-markdown
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1-1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: discover-other-people-s-pages, visit-a-specific-person-s-page-by-url
- Blocked by: user-registration-and-username-claim
- Soft: —

**Description:**

Design and implement homepage content storage (schema: username, parsed HTML from markdown, raw markdown source, updated_at timestamp). Integrate markdown parser (commonmark or similar; team choice). Store raw markdown, render to HTML on read. No real-time preview yet — v1 is edit-and-save.

**Acceptance:**
- Homepage table stores username, raw markdown, rendered HTML, updated_at
- Markdown parser correctly converts common markdown to HTML
- Raw markdown is persisted and can be retrieved for editing
- Rendered HTML is available for serving to readers
- XSS attack vectors in markdown are blocked (sanitize HTML output)

**Risk:**

Markdown-to-HTML rendering can be a security surface (XSS via markdown input). Use a well-tested library and sanitize output.
