## Scenario 016: Rate-limit and lockout events produce no observable telemetry — Queen ruling #3 violated

**Severity:** silent-wrongness

**Setup:**

The rate limiter fires (either IP throttle or email lockout), the service returns a 429 or 423 HTTP response. The FailedAttempt table has an entry for the credential failure. But there is no event emission, no metric increment, no observability hook. The Dormouse has no way to observe: 'which IPs are currently rate-limited?', 'how many accounts are locked?', 'is the attack still active?'

**Trigger:**

An active credential-stuffing attack generates 4,000+ login attempts over 8 minutes. The rate limiter catches them; the responses are 429 and 423. Production telemetry shows only HTTP status codes.

**Expected:**

For each rate-limit or lockout decision, an observable event is emitted (log entry, metric increment, or event queue). The Dormouse can query: rate-limit events per IP (cardinality: IP → event count), lockout events per email (cardinality: email → event count), unlock events (cardinality: email → when), attack-window success count (cardinality: email → success/total).

**Concern:**

The Queen's ruling #3 explicitly requires 'production telemetry required before v1 ship'. The current implementation produces no telemetry. The breach-notification ruling #4 depends on knowing 'which credentials succeeded during the attack window'—that requires instrumentation for successful login *during* rate-limit/lockout activity, which is not present.

**Property:**

For all rate-limit decisions and account-lockout decisions, an observable event must be emitted at the time the decision is made, with sufficient context (email, source_ip, threshold, window-expires-at) for the Dormouse to construct post-incident observability.

**Implies:**
- Implies a contract negotiation (per Pair Protocol) between the Tweedles and Dormouse. The rate limiter must emit events; the Dormouse must define the event schema. This contract must be negotiated before implementation resume.
- Implies that the current implementation cannot satisfy the Queen's ruling #3 without additional instrumentation work. The code that's shipped is incomplete against the Queen's requirements.
