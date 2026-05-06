# ADR-001: Decouple unlock authorization from initial authentication

## Context

Credential-stuffing attack in progress. Rate-limiting will slow the attack but not stop it entirely. When a user is locked out, they must be able to regain access by proving account ownership. The only credential they have is the one that just failed (password) — which is now known to be compromised. Trusting password alone for unlock would allow the attacker to unlock stolen accounts, defeating the lockout. Alice's stories require frictionless, self-service unlock for legitimate owners.

## Decision

Unlock (account recovery after lockout) must require a second factor independent of password. This factor proves account ownership without trusting the compromised credential. The unlock path runs through a separate authorization primitive than the login path — it may be email-based (send reset link to account email), SMS-based (OTP to registered phone), or security-question-based, but it must not accept the login password as proof of ownership.

## Tradeoffs

- Unlock is async or partially-async (email link or SMS OTP takes time); users wait 5-30 minutes instead of immediate re-entry. Alice's 'without waiting forever' story requires SLA clarity on this.
- Unlock requires the user to have access to a recovery channel (registered email or phone). If they don't, they fall into support. This is acceptable if the recovery setup happens at signup and is mandatory.
- If email-based recovery, we depend on email deliverability (spam filters, infrastructure availability). If SMS-based, we depend on SMS carrier reliability and add cost.
- Recovery primitives may not exist in the codebase yet. Building during incident response adds risk and scope creep. This must be clarified before the Tweedles start the unlock UX.
- If the recovery primitive already exists and is used elsewhere (password reset flow?), we reuse it and the cost is lower. If it doesn't exist, we are adding a new service, which carries design and operational risk during an active incident.

## Status

Proposed
