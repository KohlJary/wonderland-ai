## Scenario 005: Monitoring detects the next credential-stuffing variant before Dormouse telemetry spike reaches severity=high

**Severity:** curiosity

**Setup:**

Next attack uses distributed botnet (50 IPs, each sending 40 requests/min) instead of single IP. Attack pattern: same-username repeated across 50 IPs (e.g., 'admin' from IPs 192.0.2.1–192.0.2.50), or distinct-usernames again but now per-IP rate is lower and no single IP triggers threshold.

**Trigger:**

Distributed credential-stuffing attack begins.

**Expected:**

Monitoring rule triggers on: (1) sum of failed_login_count across all IPs over 5-min window > threshold, (2) distinct_usernames in failed login set > threshold, (3) success_rate drops below normal baseline. Alert fires before 47 users are locked out.

**Concern:**

The current attack was caught because Dormouse telemetry monitors global auth failure rate and single-IP patterns are obvious. A distributed attack spreads the load and hides in per-IP noise. The question is: can we detect this variant before the lockout cascade?

**Property:**

For all distributed credential-stuffing attacks characterized by {low per-IP request rate, high distinct-username count, anomalous success_rate drop}, there exists a monitoring rule that fires within 5 minutes of attack start.

**Implies:**
- Implies Dormouse: design monitoring rule for distributed variant (sum-based, username-diversity-based, not just single-IP pattern matching)
