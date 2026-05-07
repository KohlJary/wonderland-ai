## Ticket 006: Homepage discovery listing (first cut)

**Sources:** discover-other-people-s-pages
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1-1.5 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: view-user-homepage-by-username-url
- Soft: edit-homepage-flow-form-save

**Description:**

Backend endpoint to list all homepages: `GET /discover`. Return paginated list of usernames + preview (first 200 chars of rendered HTML). No recommendation algorithm, no filtering, no search — just a chronological list of recently-updated homepages. Frontend renders as a simple list with links to each homepage.

**Acceptance:**
- GET /discover returns paginated list of homepages (10 per page, default)
- Each entry includes username, updated_at, and 200-char preview of rendered HTML
- List is ordered by most-recently-updated first
- Pagination cursor is stable (can fetch page 2, then page 1 again)
- Frontend renders list as clickable links to user homepages

**Risk:**

Pagination without cursor-based implementation can cause skips/duplicates under concurrent updates. Use cursor pagination (updated_at + id) not offset.
