## Scenario 003: Attacker rotates User-Agent strings to bypass any rate-limit keyed only on IP+User-Agent combo

**Severity:** degradation

**Setup:**

Rate-limit implementation keys on (source_ip, User-Agent). Attacker sends 20 requests/min from 203.0.113.42 with User-Agent set to random string each time (request 1: 'Mozilla/5.0...', request 2: 'Chrome/90...', request 3: 'custom-bot/1.0'). Each unique UA creates a new rate-limit bucket.

**Trigger:**

Attacker changes User-Agent header on each request while maintaining same source IP.

**Expected:**

Rate-limit is keyed on source_ip alone, so rotated User-Agent does not create new buckets. Attack is blocked at IP level regardless of User-Agent variance.

**Concern:**

If rate-limit is (IP, User-Agent) composite, attacker can rotate UA every few requests and multiply effective request rate. The Dormouse's telemetry showed 'rotating User-Agent strings' — if the mitigation doesn't account for this, it's a false stop.

**Property:**

Rate-limit enforcement must be keyed on source_ip as the primary dimension, independent of User-Agent or other header variance.

**Implies:**
- Implies Tweedle backend: rate-limit counter keyed on IP alone; User-Agent rotation does not reset the counter
