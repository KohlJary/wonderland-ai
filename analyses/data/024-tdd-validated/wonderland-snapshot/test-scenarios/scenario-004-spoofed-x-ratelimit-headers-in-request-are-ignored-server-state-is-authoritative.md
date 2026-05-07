## Scenario 004: Spoofed X-RateLimit-* headers in request are ignored; server state is authoritative

**Severity:** silent-wrongness

**Setup:**

Client has made 5 requests in current bucket (5/10 quota used). Client crafts POST /api/messages with custom headers: X-RateLimit-Remaining: 100, X-RateLimit-Limit: 1000.

**Trigger:**

Request arrives with spoofed rate-limit headers.

**Expected:**

Backend ignores spoofed headers. Server-side state shows 5/10 used. Request is accepted (returns 200). Response returns actual X-RateLimit-Remaining: 4 (not spoofed 100). Next 5 requests return 200; 11th returns 429.

**Concern:**

If backend trusts spoofed X-RateLimit-* headers from request, attacker can raise X-RateLimit-Remaining to bypass rate limits entirely (silent wrongness — enforcement is gone). Frontend assumes response headers are authoritative; if backend reflects client headers, frontend UI shows wrong rate-limit state.

**Property:**

For all requests R with spoofed rate-limit headers, response X-RateLimit-* values are derived from server state, not from request headers.

**Implies:**
- Implies header validation must happen early in middleware — contract-004.
