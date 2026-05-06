## Scenario 004: Silent wrongness — rate-limit bypass via distributed attack across many IPs on same email

**Severity:** silent-wrongness

**Setup:**

Attacker has a botnet with 100 compromised hosts across different IP ranges (all with rotating User-Agent strings to defeat IP+UA fingerprinting). The attacker wants to try 50 password guesses against alice@example.com.

**Trigger:**

The attacker sends 50 concurrent POST /login requests, each from a different source_ip in the botnet, all with email='alice@example.com' but different passwords.

**Expected:**

The per-IP rate limit does not apply (each IP makes only 1-2 requests). The per-email account lockout should trigger after 5 failed attempts, regardless of which IP they come from. After the 5th failed attempt, alice@example.com should be locked out for 15 minutes, preventing further password guesses from any IP.

**Concern:**

If the mitigation implements only per-IP rate limiting and neglects per-email account lockout, the system will not stop distributed attacks. The attacker bypasses the IP limit by distributing requests. Without account lockout, the password-guess iteration continues at full speed.

**Property:**

For all emails E, failed login attempts from any source_ip should be counted toward an email-level lockout threshold. Account lockout is independent of source_ip.
