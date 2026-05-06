## Story 012: Attacker with the breached password cannot use the unlock flow to regain access to stolen accounts

**Persona:** The attacker (not a person, but a persona). They have 4,127 credentials from a leaked list. They want to unlock the accounts they couldn't brute-force during the 8-minute attack window. If the unlock flow reuses password-based auth, they can just unlock the stolen accounts the same way they tried to attack them.

**Situation:**

The attacker attempts to unlock a stolen account using the unlock flow. They enter the compromised email address and attempt to verify account ownership. The system must not issue them an unlock token if their only proof of ownership is 'I know the password.'

**Need:**

As the system (protecting against the attacker), I need an unlock path that proves account ownership through a mechanism the attacker cannot satisfy with just the breached password, so that unlock becomes a recovery mechanism for legitimate users and not a second vector for the attacker.

**Acceptance:**
- The unlock flow does NOT accept the breached password as proof of account ownership
- The unlock flow requires an additional factor that the attacker is unlikely to possess: email access (verified via link), SMS access (verified via code), recovery code (printed at account setup), or security question (answer known only to the account owner)
- If an attacker attempts to unlock an account 3+ times without providing the correct additional factor, their IP is rate-limited from future unlock attempts
- Legitimate account owners can still provide the additional factor and unlock within 5 minutes; the attacker cannot
- If the additional factor is email-based, the unlock link is single-use and expires after 15 minutes; the attacker cannot replay captured links
- Logs record every unlock attempt (successful and failed) so the Queen can later investigate whether the unlock flow itself was used as a secondary attack vector

**Tier:** core

**Confusion-flags:**
- The acceptance criteria are about security properties, not user experience. But Alice's job is UX, not security architecture. I'm stepping into the Queen's domain to surface what a 'defensible' unlock looks like from the attacker's perspective. This story should probably be co-written with the Queen or the Cat, not just Alice.
- If the primary factor is email-based, and the attacker controls the email account (because the breach was broad enough to include email passwords too), the unlock path fails. But the stories don't address this doomsday case. The team may need a decision on 'what if the breach included email credentials too?'
- The 15-minute link expiry might be too short if email is delayed. The 5-minute user SLA and the 15-minute link expiry are in tension. Need to confirm which one wins.
