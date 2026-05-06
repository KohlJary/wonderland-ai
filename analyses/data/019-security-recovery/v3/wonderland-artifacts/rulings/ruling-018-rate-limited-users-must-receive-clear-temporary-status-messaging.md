## Ruling 018: Rate-limited users must receive clear, temporary-status messaging

**Severity:** medium
**Domain:** data-handling
**Source:** story slug=legitimate-user-on-shared-ip-experiences-rate-limiting-during-credential-stuffing-attack-needs-to-understand-it-s-temporary

**Citation:**

OWASP A01:2021 Broken Access Control (rate-limiting is a legitimate access control); CWE-799 Improper Control of Interaction Frequency. Users rate-limited on shared IPs (corporate networks, universities, coffee shops) may believe the service is broken or that their account is compromised, leading to support volume spikes, account-abandonment, and user frustration that could have been prevented with clear messaging.

**Finding:**

When a legitimate user on a shared IP hits the per-IP rate limit (10 requests/minute), they receive a 429 Too Many Requests response with no explanation. They do not know whether this is a service error, a permanent ban, or a security measure protecting them. In the absence of clear messaging, they will assume the worst, attempt workarounds (VPN, alternate device, calling support), or abandon the login attempt entirely. This creates unnecessary user friction and inflates support load during an ongoing incident.

**Required Remediation:**

When a user hits the per-IP rate limit, the 429 response must include a human-readable explanation that (a) names the rate limit as a temporary security measure in response to an active attack, (b) specifies the expected wait time before they can retry (derived from the sliding-window reset time), and (c) provides a workaround if available (e.g., 'try again in X minutes' or 'use a different network if available'). The explanation must be visible in the error page/API response, not hidden in HTTP headers.

**Acceptance Criteria:**
- 429 response includes a user-facing error message (not just an HTTP status code)
- Message explicitly names rate-limiting as a temporary security measure in response to the active attack
- Message includes a specific time when the user can retry (e.g., 'Please try again after 14:35 UTC')
- Message suggests a workaround if feasible (e.g., 'If you have access to a different network, you may be able to log in immediately')
- User testing confirms users understand the message is temporary and not a permanent service failure

**Residual Risk:**

Some users will still experience frustration; rate-limiting creates friction by design. The residual risk is mitigated by making the friction intentional and transparent rather than mysterious. This is acceptable.

**Compliance Implications:**

GDPR Art. 5 (transparency): users have a right to understand why their access is being restricted. This ruling ensures the restriction is transparent and clearly tied to a security incident, not a service malfunction.

**Audit Reference:**

Ruling issued during credential-stuffing incident response. Rate-limit messaging required before rate-limiting ships to production.
