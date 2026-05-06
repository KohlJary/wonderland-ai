## Story 004: User experiencing the attack in real-time (failed login attempts from their own location/device) needs help distinguishing their own error from a compromise

**Persona:** Casey, 26, just remembered they need to check something in the service. Typed their password wrong three times in a row (it's been a week since they logged in last). On the fifth attempt, the account locks. Casey now believes their password has been compromised and considers changing it, but also wonders if they're being too paranoid.

**Situation:**

Casey is the false positive case — they are not under attack, but they just triggered the lockout mechanism by making their own repeated typing mistakes. They need to understand what happened, confirm their account wasn't actually compromised, and get back to what they were doing.

**Need:**

As Casey, I want to know that my account lockout is due to my own repeated failed attempts (not an attacker), so that I can unlock my account and move on without unnecessary alarm or forced password changes.

**Acceptance:**
- When lockout occurs, the service shows which IP address triggered it and when (so Casey can verify it matches their device/location).
- The unlock flow is fast and non-alarming (does not suggest a security incident if this was user error).
- The service does not force a password change unless there is actual evidence of compromise (e.g., successful login from a different location, or a password that matches a leaked-credentials list).

**Tier:** core

**Confusion-flags:**
- I'm uncertain about the balance between security (force password change after lockout) and user experience (don't force it if the user caused the lockout themselves). This is exactly the kind of tradeoff the Queen should be explicit about in her ruling.
- I also don't know whether the service currently tracks 'successful login from unusual location' — if it doesn't, then we can't offer that as evidence of compromise. This might be a gap the Dormouse needs to fill with observability improvements.
