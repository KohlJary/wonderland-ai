## Ticket 009: Homepage discovery feed (recent activity)

**Sources:** discover-other-people-s-homepages, see-the-most-recently-active-homepages-alternative-to-directory
**Owner:** Tweedledum
**Tier:** fast-follow
**Estimate:** 1.5–2.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: public-homepage-view-and-http-delivery
- Soft: —

**Description:**

Public feed showing the N most recently published homepages (e.g., updated in the last 7 days). No user accounts are required to view. Fast-follow because it is a convenience feature and does not block core functionality (sign up → publish → share). Include pagination or infinite scroll.

**Acceptance:**
- Public endpoint GET /discover returns a list of recently updated homepages
- List includes slug, author email (if public), update timestamp
- Pagination or infinite scroll works without auth
- Most recent updates appear first

**Risk:**

Query performance on large datasets; may need indexing on (updated_at, slug).
