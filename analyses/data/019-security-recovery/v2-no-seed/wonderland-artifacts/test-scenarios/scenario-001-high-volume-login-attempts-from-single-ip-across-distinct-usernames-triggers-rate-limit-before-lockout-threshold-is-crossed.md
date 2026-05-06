## Scenario 001: High-volume login attempts from single IP across distinct usernames triggers rate-limit before lockout threshold is crossed

**Severity:** breakage

**Setup:**

Production system with /login endpoint and rate-limit middleware in place. Attack begins: attacker IP 203.0.113.42 sends 50 login requests/second across rotating username list. Current lockout threshold is 5 failed attempts per user.

**Trigger:**

Attacker sends wave of 100+ requests in rapid succession from single source IP, each targeting a different username.

**Expected:**

Rate-limit middleware rejects requests after threshold (e.g., 20 requests/min from single IP) with 429 Too Many Requests. User lockout state machine does NOT increment. Legitimate users from that IP segment are NOT collateral-locked.

**Concern:**

Without IP-level rate-limiting, the per-user lockout counter becomes the attack's metering — attacker can enumerate a 2,800-username list and lock out ~560 accounts (2800 / 5) while still operating. The current system stops the attacker via user lockout as a side effect, not via defense-in-depth.

**Property:**

For all login-attempt patterns P where source_ip(P) is constant and distinct_usernames(P) > threshold_T: rate-limit(source_ip) must trigger before sum of per-user lockout increments across all users in P exceeds lockout_threshold.

**Implies:**
- Implies immediate Queen ruling: IP-level rate-limit shape (requests/time), exemption policy for legitimate shared IPs (office networks, VPNs), lockout-threshold adjustment
- Implies Tweedle backend implementation: rate-limit middleware before login handler, IP-keyed counter, 429 response shape
- Implies Tweedle frontend: 429 handling — user sees 'too many attempts from your network, try later' not 'account locked'
