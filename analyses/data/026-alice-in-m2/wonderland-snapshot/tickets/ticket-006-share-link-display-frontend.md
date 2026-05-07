## Ticket 006: Share link display (frontend)

**Sources:** share-my-homepage-link-and-know-people-can-visit
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 90% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: public-homepage-view-and-http-delivery
- Soft: —

**Description:**

After publish, show a 'Share your homepage' section with the full URL, a copy-to-clipboard button, and QR code (optional but nice-to-have). Make it obvious and prominent so users see it immediately after publishing.

**Acceptance:**
- After publish, user sees a 'Share' section with their full URL
- Copy-to-clipboard button copies the URL
- URL is correct and clickable
- Optional: QR code encodes the URL and displays visibly

**Risk:**

QR library dependency; skip in v1 if it adds complexity.
