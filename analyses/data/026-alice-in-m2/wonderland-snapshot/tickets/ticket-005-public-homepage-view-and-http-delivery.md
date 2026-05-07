## Ticket 005: Public homepage view and HTTP delivery

**Sources:** visit-someone-else-s-homepage-and-know-it-s-real, share-my-homepage-link-and-know-people-can-visit
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: markdown-publishing-setup
- Soft: frontend-markdown-editor

**Description:**

Public endpoint: GET /homepage/:slug returns a fully-rendered HTML page (not an API). Page includes the published markdown content, user's slug in the header, and a 'made with homepages.test' footer. Page is cacheable (Cache-Control headers). No authentication required. User can share the full URL with anyone and they see the published page.

**Acceptance:**
- GET /homepage/:slug returns 200 with rendered HTML
- Page includes the published markdown content
- Page displays the slug (so visitor knows the URL is the canonical one)
- Cache-Control headers are set (e.g., public, max-age=3600)
- Nonexistent slugs return 404

**Risk:**

None identified; this is straightforward rendering.
