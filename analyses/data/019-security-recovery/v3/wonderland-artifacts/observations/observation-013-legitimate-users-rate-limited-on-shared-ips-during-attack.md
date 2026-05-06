## Observation 013: Legitimate users rate-limited on shared IPs during attack

**Type:** incident
**Severity:** sev2
**Time window:** 2024-05-05T14:23:00Z — 2024-05-05T14:58:00Z

**Symptom:**

Rate-limit decision fired 247 times on IPs with concurrent attacker traffic. Source IPs: corporate (2 ranges, 89 sessions), university (1 range, 104 sessions), shared office (24 IPs, 54 sessions). Per-IP limit threshold (10 req/min) reached before per-email lockout on attacker accounts. Users received 429 responses; legitimate retry succeeded after 60s window elapsed or on different network.

**Affected scope:**

Legitimate users on shared IP ranges during attack window. Geographic distribution: US East (corporate + university), US West (office networks). Estimated user count: 247. Session impact: temporary (60s–few minutes), recoverable without intervention.

**Evidence:**
- Dashboard: Rate-limit events by source IP, 14:23–14:58 UTC, filtered for IPs with both 429s and failed credentials
- Query: SELECT source_ip, COUNT(*) FROM rate_limit_events WHERE fired_at BETWEEN '2024-05-05T14:23:00Z' AND '2024-05-05T14:58:00Z' GROUP BY source_ip HAVING COUNT(*) > 10
- Session logs: 247 sessions with 429 response followed by successful auth after 60s or from different IP
- FailedAttempt logs: attacker credentials on same IPs, attempt pattern consistent with credential-stuffing tooling (1–2s intervals, many usernames, few passwords)

**Probable domain:** frontend + observability

**Routed to:** alice (user experience consequence); dormouse (confirms metric accuracy)
