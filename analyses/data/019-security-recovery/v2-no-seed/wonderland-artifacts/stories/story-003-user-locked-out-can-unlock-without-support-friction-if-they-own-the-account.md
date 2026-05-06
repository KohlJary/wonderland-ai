## Story 003: User locked out can unlock without support friction if they own the account

**Persona:** Dev, 31, a contributor who tried to log in, got locked, and doesn't want to wait or email support — he just wants back in.

**Situation:**

Dev hit his 5th failed login. He's locked out. He remembers his password now. He doesn't want to email support and wait. He wants to unlock himself.

**Need:**

As Dev, I want to unlock my account myself — either by waiting a fixed time and trying again, or by clicking a link in a confirmation email, or by resetting my password — without having to contact support.

**Acceptance:**
- User sees a clear unlock path on the locked-account error screen
- Path is immediate (e.g., 'unlock in 15 minutes') or self-service (e.g., 'reset password to unlock now')
- If time-based, a countdown timer shows remaining wait time
- If password-reset-based, a link sends reset email immediately and explains 'reset password to unlock'

**Tier:** core

**Confusion-flags:**
- I don't know what the lockout policy will be — 15 minutes? 1 hour? Self-reset? The Queen will rule this. Whatever she rules, the UX has to match it immediately.
- I don't know if we can safely auto-unlock after X minutes, or if that's a security risk. If the attack is still active, maybe we don't unlock automatically — maybe we require a password reset to prove it's the real owner. That's a Queen call, and it changes the UX significantly.
- I don't know if the user can reset their password while locked out, or if the password reset flow is separate from the login flow. If they're separate, the error message has to route users to password reset clearly.
