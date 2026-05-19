## Ruling 002: Server CRUD endpoints must enforce note ownership and validate tag associations before persistence

**GUID:** 01KRXRSQR83W3G0X5FS0V7WZ86
**Severity:** high
**Domain:** authorization
**Source:** proposal: client-buffered, server-authoritative note persistence

**Citation:**

OWASP A01:2021 Broken Access Control; CWE-639 Authorization Through User-Controlled Key. Server does not yet name authentication model; assuming single-user MVP, but endpoint implementation must not accept arbitrary user_id from client.

**Finding:**

The proposal treats the server as source of truth for note state. If the CRUD endpoints accept note_id and user_id as untrusted client input without validating the authenticated session, an attacker can modify or read notes belonging to other users (or to unauthenticated sessions). Similarly, if tag associations are not validated (e.g., client sends tag_id without checking the tag exists or belongs to this user), the endpoint could create orphaned tag references or corrupt the tag index.

**Required Remediation:**

1) Every note CRUD endpoint must extract the authenticated user from the session/JWT, not from client payload. The client may send note_id; the server must verify that note_id belongs to the authenticated user before allowing read/write/delete. 2) Tag associations in create/update requests must be validated: verify each tag_id exists, belongs to this user, and the association is not a duplicate. Reject invalid tag_ids with 400 Bad Request, not silent ignoring. 3) Document the auth model (session, JWT, API key) in the ADR or contract note; the Tweedles must implement against a named contract.

**Acceptance Criteria:**
- Authenticated user identity is extracted server-side from session or token, not client payload
- Unauthorized CRUD requests (accessing another user's note) return 403 Forbidden
- Tag association with non-existent or unowned tags is rejected with 400 Bad Request
- Caterpillar review confirms note_id ownership check in every endpoint implementation

**Residual Risk:**

Single-user MVP has no multi-user auth framework yet. This ruling applies the *principle* of ownership validation (when multi-user auth arrives, it slots in cleanly). For M1 single-user, the server can treat all requests as coming from a single implicit user; the *pattern* of validating ownership is still required so it's not retrofitted later.

**Compliance Implications:**

If notes are later expanded to store personal or experimental data, ownership enforcement is foundational to GDPR-compliant access control (Art. 32, security of processing).

**Audit Reference:**

Authorization threat model for single-user note app; ruling applied to server-authoritative proposal.
