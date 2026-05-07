## Ticket 005: View user homepage by username URL

**Sources:** visit-a-specific-person-s-page-by-url
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5-1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: discover-other-people-s-pages
- Blocked by: homepage-schema-and-markdown-parsing
- Soft: —

**Description:**

Implement public read-only route: `GET /{username}`. Look up user by username, fetch homepage record, render stored HTML. No authentication required; anyone can view. Return 404 if user doesn't exist. Simple endpoint.

**Acceptance:**
- GET /{username} returns rendered homepage if user exists
- Rendered HTML is served from stored content
- GET /{non-existent} returns 404
- No authentication required to view homepage
- Page title and metadata reflect the user's username

**Risk:**

Low risk — this is a straightforward read. Watch for case-sensitivity on username lookups (decide: case-insensitive or not).
