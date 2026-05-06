## Observation 011: Distributed-IP attack surface: email-based rate-limiting absent; per-IP limiting alone insufficient against botnet-style enumeration.

**Type:** anomaly
**Severity:** sev3
**Time window:** 2026-05-05T14:23:00Z — ongoing

**Symptom:**

The current attack is single-IP (or few IPs); the per-IP rate-limiter is effective. However, the Hatter's scenario #4 and Queen's ruling on distributed-IP bypass surface a known-gap: an attacker with a botnet or proxy list can iterate across many IPs targeting the same email address, and the per-IP limit will not stop them. The per-email lockout (5 failures) will eventually catch them, but only after 5 successful attempts per IP * N IPs—a much higher bar than a single-IP attack. The implementation currently has no email-based rate-limiting (e.g., max 20 login attempts per email per 5-minute window), which would catch distributed enumeration faster. The Cat's ADR frames this as 'fast-follow' (post-incident), and the Queen's ruling #1 does not explicitly mandate email-based rate-limiting for v1. But this is a silent-wrongness gap: the system will look like it's defending against the attack (lockout counter increments) while distributed attacks proceed efficiently. Observability will reveal this only after the attack is underway.

**Affected scope:**

/login endpoint; authentication service; credential-enumeration attacks from distributed sources

**Evidence:**
- Hatter's test_scenario #4: 'Silent wrongness — rate-limit bypass via distributed attack across many IPs on same email'
- Cat's ADR-001: frames email-based rate-limiting as 'known gap, fast-follow'
- src/auth/rate_limit.py: implements IP-based rate-limiting only; no per-email rate-limiting logic
- Attack telemetry (current): single-IP or few IPs, so per-IP limiter is effective; does not yet reveal the distributed-IP surface

**Probable domain:** architecture

**Routed to:** cheshire_cat
