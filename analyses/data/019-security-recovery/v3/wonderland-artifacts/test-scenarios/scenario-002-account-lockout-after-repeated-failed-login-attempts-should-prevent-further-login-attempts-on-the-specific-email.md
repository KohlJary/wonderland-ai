## Scenario 002: Account lockout after repeated failed login attempts — should prevent further login attempts on the specific email

**Severity:** breakage

**Setup:**

A known user with email='alice@example.com' and password='correct horse battery staple'. An attacker has the email but not the password and iterates through 10 password guesses from the same IP.

**Trigger:**

POST /login with email='alice@example.com' and 10 consecutive wrong passwords from IP 10.0.0.1, each 1 second apart.

**Expected:**

After 5 failed attempts on the same email (the current lockout threshold before the incident), subsequent /login attempts with that email should return 401 with a message saying the account is temporarily locked, regardless of whether the password is correct. The lockout should be time-scoped (e.g., 15 minutes) and lift automatically, or require admin unlock.

**Concern:**

Currently, the FailedAttempt log exists but nothing reads it to enforce lockouts. An attacker can iterate through password guesses against a known email indefinitely (up to the per-IP rate limit, if that exists). Once the per-IP limit is in place, the attacker will switch IPs to get more attempts against the same email. Account-level lockout is the second line of defense.

**Property:**

For all emails E with a registered user, if FailedAttempts with email=E exceed M failed attempts in a rolling T-minute window, subsequent POST /login requests with email=E should fail with a lockout error for at least S seconds, independent of password or source_ip.

**Implies:**
- Implies architectural decision on lockout duration and exemptions (can the real user reset their password while locked? can an admin unlock?) — flag for Cat.
- Implies security ruling on lockout disclosure (should we tell the user via email that their account is locked? risk of account enumeration) — flag for Queen.
