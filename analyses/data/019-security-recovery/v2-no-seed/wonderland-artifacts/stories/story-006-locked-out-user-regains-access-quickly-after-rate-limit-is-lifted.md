## Story 006: Locked-out user regains access quickly after rate-limit is lifted

**Persona:** Jordan, 28, accountant, locked out of their work account after being on a shared office IP during the attack. The attack is over. Their password was never compromised. They just need back in.

**Situation:**

Jordan tried to log in during the attack window, hit the rate-limit, and got locked out. The attack lasted 8 minutes. It's been 90 seconds since the rate-limit stopped the attack. Jordan's email inbox has a notification that their account was locked; they want to log back in immediately without friction or waiting.

**Need:**

As Jordan, I want to unlock my account in under 30 seconds without needing to call support or wait for an email, so that I can get back to the work I was doing.

**Acceptance:**
- Unlock is available via the login page ('Unlock Account' button is visible to any user who sees a lockout error)
- Unlock flow validates account ownership via email link (token-in-URL, 15-minute expiry)
- After successful unlock validation, account is immediately unlocked and user can log in with existing password
- Total unlock time from click-to-relogin is under 30 seconds (email delivery + link click + form submit)
- User does not need to change their password as part of unlock (the breach investigation confirmed zero successful logins)

**Tier:** core

**Confusion-flags:**
- Jordan's experience here is different from the 'compromised credential' persona I published earlier — that persona doesn't exist in this incident because the Dormouse confirmed zero breaches. I'm keeping that persona as a fast-follow (it matters for the threat model), but shipping a story optimized for the actual incident first.
- The 15-minute email-link expiry is a guess at what's reasonable; the Queen or Caterpillar might have a security-hardening opinion here (shorter expiry = more secure but more friction if email delivery is slow).
