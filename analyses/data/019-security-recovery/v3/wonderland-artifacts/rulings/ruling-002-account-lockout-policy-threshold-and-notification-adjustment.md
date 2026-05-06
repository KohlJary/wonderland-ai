## Ruling 002: Account lockout policy — threshold and notification adjustment

**Severity:** critical
**Domain:** authentication
**Source:** Dormouse observation; 47 accounts already locked due to 5-attempt threshold being too aggressive during active attack

**Citation:**

CWE-307 Improper Restriction of Rendered UI Layers or Frames; NIST SP 800-63B: account lockout should balance security (rejecting attackers) against usability (not locking legitimate users). Current threshold of 5 failures is too aggressive during active credential-stuffing; legitimate users with 5 failed attempts in rapid succession are collateral damage.

**Finding:**

Current lockout threshold (5 failed attempts) is appropriate for normal conditions but becomes a denial-of-service vector during active attack. The 47 locked accounts represent users who may have tried to log in during the attack window and coincidentally crossed the threshold. These users cannot self-unlock; support ticket load will spike. The threshold is compounding harm to legitimate users while the attacker is unaffected (they move to the next IP or username).

**Required Remediation:**

Adjust lockout threshold to 15 failed attempts within any 30-minute window (not cumulative). This reduces false-positive lockouts of legitimate users during traffic spikes. Additionally: implement user-initiated account unlock via email verification — users locked out can receive an unlock link they can self-serve, reducing support load. The unlock link must be single-use, time-bounded (1 hour), and logged.

**Acceptance Criteria:**
- Account lockout threshold updated to 15 failures / 30-minute window
- User-initiated unlock flow implemented: locked users receive email with single-use, time-bounded unlock link
- Unlock events are logged with user_id, unlock_method (email-link), timestamp, success/failure
- The 47 currently-locked accounts are manually unlocked immediately (support action, logged)
- Dormouse confirms in telemetry: no new account lockouts from legitimate users in the 1-hour window after deployment

**Residual Risk:**

Email-based unlock is vulnerable to compromise of email account. Acceptable for now; long-term, add SMS or authenticator-based unlock. The unlock link itself must not be stored in plaintext (hash it); verify this in Caterpillar's review.

**Compliance Implications:**

None direct, but lockouts affect user access rights, which affects audit trail completeness. Ensure unlock events are logged.

**Audit Reference:**

Lockout threshold change log; unlock link issuance and verification logs; the 47 manual unlocks, with reason noted
