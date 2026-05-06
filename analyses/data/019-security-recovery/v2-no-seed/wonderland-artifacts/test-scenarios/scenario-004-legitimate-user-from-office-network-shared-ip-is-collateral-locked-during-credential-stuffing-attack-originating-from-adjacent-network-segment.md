## Scenario 004: Legitimate user from office network (shared IP) is collateral-locked during credential-stuffing attack originating from adjacent network segment

**Severity:** degradation

**Setup:**

Office network NAT gateway is 203.0.113.0/24. Credential-stuffing attack originates from 203.0.113.42. Legitimate employee Alice at 203.0.113.50 on same office network attempts to log in at 14:05 UTC, while attack is ongoing from .42 at 14:03–14:11 UTC.

**Trigger:**

Alice's login request from 203.0.113.50 arrives while IP-range rate-limit is triggered on 203.0.113.0/24 (if the mitigation uses overly broad IP range).

**Expected:**

Rate-limit is keyed on exact source IP (203.0.113.50), not on /24 range. Alice's login succeeds. Only .42 is rate-limited.

**Concern:**

If the Queen's ruling specifies rate-limit on IP /24 or ISP-level ranges to catch botnet-style attacks, legitimate users from the same office network get collateral damage. This is a real tension: precision vs. coverage.

**Property:**

Rate-limit precision should be at /32 (single IP) granularity by default. Range-based rate-limiting (e.g., /24) should only be applied when attack source has been confirmed to be a botnet or when explicitly ruled by policy.

**Implies:**
- Implies Queen ruling: decision on IP granularity (single IP vs. range), trade-off between stopping attackers and collateral-blocking legitimate users from shared networks
- Implies Tweedle frontend: if legitimate user from office network is rate-limited, provide escalation path ('contact security team if you're on shared office network')
