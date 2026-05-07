## Ticket 008: Account settings and profile view

**Sources:** view-my-own-account-settings-and-profile
**Owner:** Tweedledee
**Tier:** fast-follow
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: session-management-and-auth-persistence

**Description:**

Authenticated user page showing: current email, username/slug, link to published homepage, logout button. In fast-follow (not v1) because account management is secondary to publishing. Unblock the v1 critical path (sign up → publish → share) first.

**Acceptance:**
- Authenticated user can view their account page
- Account page shows email and slug
- Account page has a link to their published homepage
- Logout button is present and functional

**Risk:**

None identified; straightforward display work.
