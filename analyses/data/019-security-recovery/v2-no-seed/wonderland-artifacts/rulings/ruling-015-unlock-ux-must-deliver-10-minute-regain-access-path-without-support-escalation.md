## Ruling 015: Unlock-UX must deliver <10-minute regain-access path without support escalation

**Severity:** high
**Domain:** authentication
**Source:** Alice's user stories (turns 4, 8, 10) — locked-out users need clear, fast recovery; acceptance criteria are measurable

**Citation:**

User-experience standards for account-recovery flows; NIST SP 800-63B (authentication) recommends account recovery be 'usable and defensible.' <10min regain-access is both.

**Finding:**

Alice has published acceptance criteria for the unlock UX ('regain access within 5 minutes, no support friction'). The team has built the rate-limit and lockout correctly, but the unlock UX spec is incomplete. Unlock must be fast enough that users regain access before support queues grow unmanageable.

**Required Remediation:**

Unlock-UX implementation must: (1) Display clear, actionable error to locked-out users; (2) Link directly to 'Unlock my account' without support friction; (3) Email token arrives within 2 minutes; (4) Token validation is <100ms; (5) Successful token validation issues session immediately (no queue, no additional verification); (6) Median end-to-end unlock time is <10 minutes from first unlock request.

**Acceptance Criteria:**
- Error message clearly states 'Account locked due to security precaution'
- Error message includes 'Unlock my account' CTA
- 'Unlock my account' initiates email-based token flow (no additional questions or friction)
- Email delivery median latency is <2 minutes
- Token validation latency is <100ms
- Token validation immediately issues authenticated session (synchronous)
- Unlock success rate is >99% for valid tokens
- Median end-to-end unlock time (request to authenticated session) is <10 minutes

**Residual Risk:**

If user's email is compromised, attacker can unlock stolen accounts. Residual risk is accepted because: (1) rate-limit already stopped the attack, (2) session revocation on password-change will terminate attacker access, (3) token TTL is short (30 min), (4) SMS fallback will be added post-incident to reduce reliance on email alone.

**Compliance Implications:**

None directly, but user-experience quality is a compliance *enabler* — locked-out users who cannot unlock quickly will escalate to support, creating triage debt and preventing the security team from investigating the breach properly. Fast, clear unlock paths are operationally necessary.

**Audit Reference:**

Ruling-015: Unlock-UX acceptance criteria specified. Acceptance by Caterpillar's review is gate before unlock-UX ships.
