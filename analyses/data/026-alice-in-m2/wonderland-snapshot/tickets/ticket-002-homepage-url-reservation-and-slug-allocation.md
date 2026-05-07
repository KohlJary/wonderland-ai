## Ticket 002: Homepage URL reservation and slug allocation

**Sources:** sign-up-and-claim-my-homepage-url
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: markdown-publishing-setup
- Blocked by: user-registration-and-email-verification
- Soft: —

**Description:**

When user completes email verification, allocate a unique URL slug (e.g., homepage.test/alice) and reserve it in the database. User sees their allocated URL and can begin writing immediately. Slug must be globally unique; collisions are rejected with a friendly 'taken' message and a suggestion to try variants.

**Acceptance:**
- User receives a unique slug after verification
- Slug appears in UI immediately (e.g., 'Your homepage: homepage.test/alice')
- Duplicate slug requests are rejected with 'already taken' message
- User can see and copy their full URL

**Risk:**

Slug collision handling under high concurrency; may need transaction isolation. Slug generation logic should be simple (no fancy heuristics in v1).
