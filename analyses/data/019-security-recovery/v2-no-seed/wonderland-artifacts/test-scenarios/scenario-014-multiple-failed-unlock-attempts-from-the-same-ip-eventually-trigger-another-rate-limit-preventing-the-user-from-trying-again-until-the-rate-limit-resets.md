## Scenario 014: Multiple failed unlock attempts from the same IP eventually trigger another rate-limit, preventing the user from trying again until the rate-limit resets

**Severity:** degradation

**Setup:**

The system enforces rate-limit on /login (10 attempts per minute per IP). The unlock flow is separate from /login (different endpoint, /unlock). But the user is behind a shared corporate IP. The legitimate user attempts unlock, token expires (scenario 2), re-requests. User makes several incorrect unlock attempts (mistyped email, stale browser cache, etc). Meanwhile, other legitimate users on the same IP are also requesting unlock. The cumulative attempts trigger a rate-limit on the unlock endpoint, if one exists.

**Trigger:**

Multiple failed unlock attempts from a shared IP exceed a rate-limit threshold (if one is enforced on /unlock).

**Expected:**

The unlock endpoint should either: (1) not enforce IP-based rate-limiting (use user_id-based instead, since the user is already authenticated to the unlock flow), or (2) have a much higher rate-limit on /unlock than on /login (because /unlock is less attackable — attacker needs the unlock token or email access), or (3) use a CAPTCHA or other proof-of-human to bypass rate-limit after a few attempts.

**Concern:**

If the unlock endpoint inherits the same rate-limit as /login (10 per minute), legitimate users on shared IPs will be rate-limited out of the unlock flow, making it worse than the original problem.

**Property:**

The unlock endpoint rate-limit (if any) is either not IP-based, or is substantially higher (e.g. 50 per minute) than the /login rate-limit, or uses user_id instead of IP as the key.

**Implies:**
- Implies operational decision on unlock rate-limit strategy (Rabbit should spec this in the ticket once Queen rules on the unlock primitive; Tweedles will implement accordingly).
