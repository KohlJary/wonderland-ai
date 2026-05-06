## Contract Note 002: Auth model: HTTP Basic vs token-based session

**State:** agreed
**Contract Version:** v1

**Current Shape:**

No auth contract yet

**Proposed Change:**

Choose between HTTP Basic (stateless, credentials per-request) or token-based (session cookie or JWT). HTTP Basic: every request includes Authorization: Basic base64(email:password). Token-based: POST /auth/login returns a token, frontend stores it, subsequent requests include Authorization: Bearer token. ADR is provisional on HTTP Basic for MVP simplicity. Proposal: HTTP Basic for v1, token-based in v1.1 if team decides production-safe logout is worth the extra complexity.

**Source:** adr/message-routing-and-user-identity (provisional auth decision)

**Frontend Impact (Tweedledee):**

HTTP Basic: frontend stores email + password (in memory; not localStorage to reduce credential exposure). On every request, base64-encodes email:password into Authorization: Basic header. Simple to implement; credentials are ephemeral (cleared on page reload). Token-based would be safer (credentials stored once, token used repeatedly; token can have expiry + refresh logic). For v1, HTTP Basic is acceptable; if team moves to tokens, frontend refactors to POST /auth/login, stores returned token in memory, includes it in subsequent requests.

**Backend Impact (Tweedledum):**

HTTP Basic for v1: every request includes Authorization: Basic base64(email:password). Backend validates on each request (no state, no token store, no expiry). POST /auth/signup (email, password, language_preference) creates user + returns 201 with user object or 400 if email exists. POST /auth/login (email, password) validates credentials + returns 200 with user object or 401 if invalid. No logout endpoint needed (logout is implicit: frontend clears credentials). No token refresh, no session management. Estimate: 1-2 days backend (straightforward HTTP Basic validation on every endpoint).

**Resolution:** Agreed v1. HTTP Basic for MVP simplicity. Frontend stores email+password in memory. Backend validates on every request. Stateless. Revisit for tokens if team wants production-safe logout (revokable tokens, expiry, refresh).

---

**History:**

- **2024-01-XX (Tweedledee propose):** Initial proposal favoring HTTP Basic; noted it's simpler but needs refactor if team moves to tokens.
- **2024-01-XX (Tweedledum propose as note-004 in parallel):** Proposed same choice; asked for frontend consent on which auth layer.
- **2024-01-XX (Tweedledee consolidate and mark agreed):** Confirmed HTTP Basic for v1, marked agreed, invited backend confirmation.
