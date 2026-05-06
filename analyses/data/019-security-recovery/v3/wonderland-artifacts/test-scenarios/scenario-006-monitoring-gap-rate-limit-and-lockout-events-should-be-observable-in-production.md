## Scenario 006: Monitoring gap — rate-limit and lockout events should be observable in production

**Severity:** degradation

**Setup:**

Rate limiting and lockout are implemented. An attacker is running a credential-stuffing campaign against the system, hitting the per-IP rate limit and triggering per-email account lockouts.

**Trigger:**

Time passes. The attacker iterates. 1 hour later, we want to know: how many distinct IPs have been rate-limited? How many accounts are currently locked? What's the distribution of failed attempts by email vs. IP?

**Expected:**

Structured logging / metrics are emitted on every rate-limit rejection and every lockout trigger. The Dormouse can query: 'how many rate-limited IPs are active right now?' and 'which accounts have been locked in the last hour?' and 'what's the failure rate trend?' Without this observability, the ops team cannot tell whether the mitigation is working or whether the attacker has shifted strategy.

**Concern:**

Rate limiting and lockout are easy to implement but easy to ship without observability. The team will deploy the mitigation, the incident will seem to resolve, and then the next incident will reveal that the attacker simply switched to a different attack vector (e.g., timing the requests to avoid the per-IP limit, or focusing on less-guarded endpoints). Observability is what lets the Dormouse wake up and tell us what's actually happening.

**Property:**

For all rate-limit rejections and all account lockouts, the system should emit structured logs with: timestamp, source_ip, email, reason (rate-limit vs. lockout), current-attempt-count, threshold-count, and time-to-reset.

**Implies:**
- Implies that Dormouse needs alerting rules for these new events — flag for Dormouse.
