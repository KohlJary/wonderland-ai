## Ticket 002: Queen's ruling: rate-limit shape, lockout threshold, breach-disclosure obligations

**Sources:** observation: Anomalous auth-failure spike from single IP — possible credential stuffing in progress
**Owner:** Queen of Hearts
**Tier:** v1
**Estimate:** 15–30 min, 90% confident (Queen's ruling is the blocker for full mitigation lock-in)
**Status:** open

**Dependencies:**
- Blocks: Implementation ticket — rate limiting and account lockout hardening
- Blocked by: —
- Soft: —

**Description:**

Incident response to credential-stuffing attack. Dormouse observation reports 4,127 failed attempts from single IP (203.0.113.42) in 8 minutes, 47 accounts locked out. Ruling needed: (1) Rate-limit shape — per-IP, per-email, or both? (2) Lockout threshold — adjust from current 5 attempts? Lockout duration? (3) Breach-disclosure obligations — did any credential-stuffing attempts succeed (clear the audit logs)? Must we disclose to affected users? Cite precedent or compliance framework in ruling.

**Acceptance:**
- Rate-limit shape is explicit (per-IP, per-email, or both)
- Lockout threshold and duration are specified
- Breach-disclosure decision is stated with citation
- Ruling is timestamped; implementation can proceed with this as contract

**Risk:**

Ruling delay extends incident response time. Mitigation can ship against an interim contract and adjust when ruling lands.
