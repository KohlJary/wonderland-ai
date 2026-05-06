## Scenario 003: Rate-limit false positives — legitimate user on shared IP during attack should not be permanently locked out

**Severity:** degradation

**Setup:**

Office network behind single NAT IP. Alice is one of 50 employees. An attacker is also attacking from the same IP (either through the same NAT or coincidentally the same public IP). Alice has made 3 failed login attempts (wrong password, typo, etc.) in the last 5 minutes — within normal human error range.

**Trigger:**

The attacker makes 20 more failed attempts from the same IP in the next 2 minutes. The per-IP rate limit triggers at (5+20)=25 attempts in 5 minutes. Alice's next login attempt is rejected with 429.

**Expected:**

Alice sees a 429 Too Many Requests and is informed that login is temporarily unavailable due to too many failed attempts. The message should suggest: (a) trying again in a few minutes, (b) using a different device/network if available, (c) requesting a password reset via email (which should not be rate-limited). Alice's account is NOT permanently locked — only the IP is rate-limited. After 5-15 minutes, she can retry from the same IP or switch networks.

**Concern:**

Overly aggressive per-IP rate limiting (e.g., lockout after 5 total attempts globally) will collateral-damage legitimate users. The rate limit must be generous enough for normal typos/forgotten-password scenarios but tight enough to stop automated attacks. The threshold and window are the key tuning parameters.

**Property:**

For all legitimate users L on a rate-limited IP, L should be able to make at least N login attempts in a T-minute window without permanent harm (i.e., the user's account remains unlocked and can be retried after the IP-level rate limit lifts).
