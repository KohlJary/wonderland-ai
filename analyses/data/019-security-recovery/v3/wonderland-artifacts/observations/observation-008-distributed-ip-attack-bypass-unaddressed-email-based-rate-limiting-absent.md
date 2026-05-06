## Observation 008: Distributed-IP attack bypass unaddressed; email-based rate-limiting absent.

**Type:** anomaly
**Severity:** sev2
**Time window:** 2026-05-05T15:12:00Z — ongoing

**Symptom:**

Implementation ships per-IP rate-limiting (10 req/min) as primary defense against attack resumption. This is effective against single-source attacks. However, Queen's ruling #1 requires email-based rate-limiting to defend against distributed-IP attacks (same target email, different attacking IPs). The implementation does not include email-based rate-limiting. Per-email lockout exists (5 failed attempts), but this is a *lockout* after compromise, not a *rate-limit* preventing compromise. The gap is observable: an attacker with a botnet can iterate across IPs targeting the same email, hitting per-IP limit on each IP (still within tolerance) while accumulating failures toward per-email lockout threshold.

**Affected scope:**

Auth service. The defense is incomplete against the escalation vector. Current attack (single IP) is stopped; next attack (distributed IPs, same target) has clear bypass.

**Evidence:**
- Tweedledee implementation includes only IP-based rate-limiting, no email-based rate-limiting
- Hatter test scenario #4 (silent-wrongness-rate-limit-bypass-via-distributed-attack-across-many-ips-on-same-email) — implementation status: not addressed
- Queen's ruling #1 — status: not met
- Cat's ADR frames per-email lockout as primary defense; implementation does not match framing

**Probable domain:** backend

**Routed to:** tweedledee
