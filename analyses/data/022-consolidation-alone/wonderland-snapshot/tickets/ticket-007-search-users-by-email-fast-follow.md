## Ticket 007: Search users by email (fast-follow)

**Sources:** adr/message-routing-and-user-identity-for-peer-to-peer-translation-chat
**Owner:** Tweedledum
**Tier:** fast-follow
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket/set-up-http-basic-auth-signup-login-endpoints
- Soft: —

**Description:**

Implement GET /users/search?q=email_or_name endpoint. Return users matching the query. For MVP, simple substring match on email and display_name. Auth check: user can search (to avoid enumeration, return only partial matches or rate-limit, TBD with Queen). This is a convenience feature for discovering conversation partners; MVP works without it (users can copy-paste emails).

**Acceptance:**
- GET /users/search?q=alice returns users with 'alice' in email or display_name
- Results do not include the querying user
- Query with 0 results returns 200 and empty array
- Unauthenticated search returns 401

**Risk:**

GDPR user enumeration concern. The Queen may require rate-limiting or result-limiting. Confirm constraints before starting.
