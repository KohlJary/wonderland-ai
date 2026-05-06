## Contract Note 004: Authentication model: HTTP Basic vs. token-based

**State:** agreed
**Contract Version:** v1 (HTTP Basic: credentials per-request, no token store, no session management)

**Current Shape:**

No auth endpoints currently; placeholder /api/messages has no auth check.

**Proposed Change:**

Implement POST /auth/signup (email, password, language_preference) and POST /auth/login (email, password). Question: stateless HTTP Basic (credentials with every request) or stateful tokens (session cookie / JWT)? ADR suggests HTTP Basic for MVP simplicity; tokens for production. Need frontend consent on what the auth layer looks like.

**Source:** ticket/set-up-http-basic-auth-signup-login-endpoints and ADR-001 (open choice on auth model)

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

HTTP Basic: validation endpoint only, no token storage/expiry logic, credentials passed base64-encoded in Authorization header. Tokens: endpoint returns a session token (JWT or session ID), frontend stores it and includes it in subsequent requests. Backend validates token on each request. Tokens require more infrastructure but enable production-safe logout and expiry. Estimate shifts from 1-2 days (Basic) to 2-3 days (tokens).

**Resolution:**

Agreed. HTTP Basic for MVP simplicity. Frontend stores email+password in memory, base64-encodes into Authorization: Basic header on every request. Backend validates on each request (stateless). No logout endpoint needed. Revisit for tokens if team wants production-safe logout.
