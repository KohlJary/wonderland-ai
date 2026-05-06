## Scenario 016: User requests unlock, receives valid token/code via email or SMS, enters token but unlock endpoint returns 'token invalid' even though token matches what was sent

**Severity:** breakage

**Setup:**

User is rate-limited after hitting the threshold (10 failed attempts in 5 minutes per Queen's ruling). User requests unlock via email or SMS. The unlock-token-send endpoint generates a token, stores it with a 10-minute TTL, and sends it to the user. User receives the token within 2 minutes. User immediately navigates to unlock endpoint and enters the token.

**Trigger:**

User submits unlock form with the correct token/code within 5 minutes of receiving it.

**Expected:**

Unlock endpoint validates the token, confirms it matches what was issued, confirms TTL has not expired, and returns 'account unlocked.' User can then log in with their password.

**Concern:**

Token validation logic has a subtle bug: the token is stored as a hash in the token table (correct), but the validation endpoint is comparing the user-submitted token directly against the hash instead of hashing the submission first. This is a classic hash-comparison bug. Result: valid tokens always fail validation. The unlock flow appears to work (user receives email, submits form, gets a response), but the response is always 'invalid token,' leaving the user locked out and unable to recover until support intervenes or the 5-minute lockout window expires.

**Property:**

For all tokens T issued with TTL > 0 at time t0, if a user submits T before t0 + TTL, the unlock endpoint must validate T and return success. The property holds for all valid tokens, not just the happy path.

**Implies:**
- Implies code-quality concern for Caterpillar: token hashing must be consistent between storage and validation. This is a classic cryptographic-comparison bug that will fail silently in testing if the test only checks the happy path.
- Implies observability concern for Dormouse: once unlock endpoints ship, we need metrics on 'unlock attempts' vs. 'unlock successes' to detect silent failures like this. If the ratio diverges (attempts >> successes), something is wrong with token validation.
