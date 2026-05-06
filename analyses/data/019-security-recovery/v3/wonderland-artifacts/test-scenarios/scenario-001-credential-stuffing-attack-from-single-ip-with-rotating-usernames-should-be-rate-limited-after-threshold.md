## Scenario 001: Credential-stuffing attack from single IP with rotating usernames — should be rate-limited after threshold

**Severity:** breakage

**Setup:**

A service with 50 known user accounts. An attacker has a leaked-credential list with real email:password pairs for 10 of them.

**Trigger:**

The attacker sends POST /login from IP 203.0.113.42 with distinct email addresses rotating through the list, at 10 requests/second for 8 minutes (4,800 attempts total across ~2,500 distinct emails).

**Expected:**

After the first 5-10 failed attempts from the same IP within a rolling time window (e.g., 5 minutes), /login should return 429 Too Many Requests. The attacker's subsequent requests are dropped without checking credentials. Legitimate users on the same IP are not affected (or see degraded service only after the same threshold is crossed).

**Concern:**

Without rate limiting on the login endpoint itself, an attacker with a credential list can brute-force the database and bcrypt at machine speed. Each failed attempt triggers a database write (FailedAttempt) and bcrypt verify (expensive). The attack will degrade login latency for all users on the same IP and may exhaust database connection pools. Even if no credentials succeed, the attack damages availability.

**Property:**

For all source_ips, POST /login rate-limited per IP should reject requests after N failures in a rolling T-minute window, without requiring the server to compute bcrypt hashes on subsequent requests from the same IP within the window.

**Implies:**
- Implies architectural decision on rate-limit scope (per-IP only? per-email? both?) — flag for Cat.
- Implies missing persona: users behind shared IP (office network, VPN, carrier NAT) who might legitimately hit the per-IP limit — flag for Alice.
