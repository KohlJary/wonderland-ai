## Test Scenario 004: CSRF Token Missing on Publish POST — Request Not Rejected

**Severity:** breakage

**Setup:**

User alice is logged in with valid session (httpOnly cookie set). Frontend has access to a CSRF token (via meta tag or GET /auth/csrf endpoint — mechanism TBD per contract-001). Frontend prepares to publish new homepage content.

**Trigger:**

Frontend POSTs /homepage/alice with {content: 'new content'} but deliberately omits the X-CSRF-Token header (simulating an attacker's site making a forged request).

**Expected:**

Backend returns 403 Forbidden. Request is rejected without executing the publish. User's homepage content is unchanged. No new content is stored.

**Concern:**

CSRF (Cross-Site Request Forgery) attack: an attacker's malicious website tricks alice's browser into making a request to this platform while she's logged in. Because the browser automatically includes her session cookie, the request appears legitimate. Without CSRF token validation, the attacker can trick alice into publishing malicious content (e.g., "Buy crypto at scamsite.com") to her homepage, damaging her reputation and misleading her followers.

Contract-001 specifies: "CSRF tokens in POST bodies or headers (specified below)" and "All POST endpoints that modify state require CSRF token in X-CSRF-Token header."

This test verifies the boundary is enforced: no CSRF token = no publish.

**Property:**

All POST/PUT/DELETE requests to state-modifying endpoints must require valid CSRF token in X-CSRF-Token header. Requests without token must return 403 Forbidden.

**Implies:**

- Requires CSRF token generation on every session (server-side, random, unpredictable).
- Requires CSRF token delivery to frontend (meta tag injection or GET /auth/csrf endpoint).
- Requires CSRF token validation: extract token from X-CSRF-Token header, compare to server-stored token for this session, reject if mismatch or missing.
- Implies test of both missing token and invalid token scenarios.
- Implies CSRF tokens are per-session (not global), so token used by alice is invalid for bob.
