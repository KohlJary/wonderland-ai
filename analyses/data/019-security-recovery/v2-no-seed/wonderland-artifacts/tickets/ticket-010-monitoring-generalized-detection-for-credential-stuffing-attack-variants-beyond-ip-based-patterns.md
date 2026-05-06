## Ticket 010: Monitoring: Generalized detection for credential-stuffing attack variants (beyond IP-based patterns)

**Sources:** test_scenario slug=monitoring-detects-the-next-credential-stuffing-variant-before-dormouse-telemetry-spike-reaches-severity-high
**Owner:** Dormouse
**Tier:** fast-follow
**Estimate:** 2-3 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket slug=implement-rate-limiting-on-login-endpoint-per-queen-ruling
- Soft: —

**Description:**

This attack came in via single-source IP + distinct usernames. The next variant will use a different signal: distributed IPs (botnet), or User-Agent rotation, or timing-based obfuscation. Rather than playing whack-a-mole with specific patterns, instrument the auth system to surface behavioral anomalies: failed-login velocity, username-enumeration signals, distribution of failures across time/IP/device. Build a dashboard where the Dormouse can see 'login failure patterns that don't match normal traffic.' The Hatter's scenario #5 (detect variant before severity=high) is the requirement. The implementation is detection infrastructure, not a specific rate-limit rule.

**Acceptance:**
- Auth system emits structured events for every failed login (username, source IP, User-Agent, timestamp, failure reason)
- Dormouse dashboard aggregates these events and surfaces anomalies (velocity, distribution, pattern shifts)
- Dormouse can see the next attack variant within 5 minutes of its beginning (not 8 minutes like this one)
- Dashboard includes alert triggers for Dormouse to escalate to the Queen when anomalies breach thresholds

**Risk:**

High. Building detection infrastructure during incident response is scope creep if not scoped carefully. This ticket is explicitly fast-follow; it should not block v1 mitigation. However, if the Dormouse signals that the immediate rate-limit is insufficient and we're expecting variant attacks in the near term, this may move to v1. Escalate to the Queen for priority decision.
