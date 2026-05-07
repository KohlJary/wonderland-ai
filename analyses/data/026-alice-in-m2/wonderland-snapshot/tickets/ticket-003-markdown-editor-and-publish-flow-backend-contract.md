## Ticket 003: Markdown editor and publish flow (backend contract)

**Sources:** write-and-publish-my-homepage-in-markdown
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 2–3 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-markdown-editor, public-homepage-viewing
- Blocked by: homepage-url-reservation
- Soft: —

**Description:**

Backend contract: User submits markdown content via HTTP endpoint. Content is stored in database, associated with user's reserved slug. GET endpoint returns published markdown as HTML or raw markdown per content-type negotiation. No editing or versioning in v1 — one write, one read. Markdown is parsed and rendered server-side; basic safety validation (no script injection) is required.

**Acceptance:**
- POST /homepage/:slug accepts markdown content and stores it
- GET /homepage/:slug returns rendered HTML
- GET /homepage/:slug?raw=true returns raw markdown
- Content updates overwrite prior content (no versioning)
- Basic XSS prevention: script tags and onclick handlers are escaped

**Risk:**

Markdown parser choice; recommend a battle-tested library (e.g., remark, marked). Large content payloads may need size limits. If real-time preview is expected, expand to 3–4 days.
