## Scenario 005: Lockout escape hatch — legitimate password-reset flow must not be rate-limited

**Severity:** degradation

**Setup:**

Alice's account is locked due to 5 failed login attempts. She has correctly remembered her password, but the account is temporarily locked. She wants to reset her password via the forgot-password flow to regain access.

**Trigger:**

POST /forgot-password with email='alice@example.com' after the account has been locked.

**Expected:**

The /forgot-password endpoint should NOT be rate-limited (or should have a much more generous rate limit, e.g., 1 request per email per hour). Alice receives a password-reset link via email. After resetting her password, she can log in again with the new password, and the account lockout is cleared.

**Concern:**

If /login rate limiting and account lockout are implemented naively, there might be confusion about what gets locked vs. what gets rate-limited. If an attacker can lock an account and then also lock the /forgot-password endpoint for that email, the legitimate user is permanently denied access. This is a denial-of-service vector.

**Property:**

For all emails E with a locked account, POST /forgot-password should remain functional and should not be rate-limited by the same mechanism that locked the account.

**Implies:**
- Implies architectural decision on password-reset flow interaction with lockout — flag for Cat.
- Implies missing feature: /forgot-password endpoint may not exist yet — flag for Rabbit.
