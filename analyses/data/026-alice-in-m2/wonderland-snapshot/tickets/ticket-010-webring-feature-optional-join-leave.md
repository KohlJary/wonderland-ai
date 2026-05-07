## Ticket 010: Webring feature (optional join/leave)

**Sources:** add-my-site-to-a-webring-if-i-want
**Owner:** Tweedledum
**Tier:** post-launch
**Estimate:** 2–3 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: public-homepage-view-and-http-delivery
- Soft: —

**Description:**

Post-launch: User can opt-in to a webring that displays previous/next links on their homepage. Webring is a collective of participating homepages; links form a circle. User decides whether to join. If joined, homepage footer includes prev/next navigation to other webring members.

**Acceptance:**
- User sees a webring opt-in toggle in account settings
- If joined, homepage footer includes prev/next links to other members
- User can leave the webring anytime
- Webring membership is durable across site updates

**Risk:**

Circular link generation logic; test thoroughly to avoid infinite loops or orphaned members.
