## Story 001: User locked out by credential-stuffing attack needs to know why and how to recover

**Persona:** Jordan, 28, regular user who checked email during lunch and found 'Account locked due to repeated failed login attempts.' They did not attempt to log in; they are confused and worried someone has their password.

**Situation:**

Jordan is trying to log back into the service after the credential-stuffing attack has swept through. Their email was on a leaked list somewhere. The attack tried their credentials multiple times in the span of 90 seconds. The lockout kicked in on attempt 5. Now they want back in.

**Need:**

As Jordan, I want to understand why my account is locked and how to unlock it, so that I can regain access without believing my security has been permanently compromised.

**Acceptance:**
- The login page shows a message explaining account lockout (not cryptic or alarming), with a clear next step (e.g., 'verify your email to unlock').
- Jordan can initiate account unlock via email verification without requiring customer support intervention.
- The unlock email arrives within 2 minutes and is clear about what happened (e.g., 'We detected repeated failed login attempts on your account. If this wasn't you, click here to unlock and change your password').
- After unlock, Jordan can log in again with their current password (no forced password change unless they choose it).

**Tier:** core

**Confusion-flags:**
- I'm uncertain whether 'password reset' should be required after unlock, or optional. A forced reset is more secure but might add friction. An optional reset is better UX but might leave a compromised password in place if the leaked credentials worked. This is a real tradeoff, not a bug.
- I don't know whether the unlock link should be single-use or time-limited. Expiry adds security (leaked unlock links can't be used forever) but might frustrate users who miss the window. This needs input from the Queen's ruling.
