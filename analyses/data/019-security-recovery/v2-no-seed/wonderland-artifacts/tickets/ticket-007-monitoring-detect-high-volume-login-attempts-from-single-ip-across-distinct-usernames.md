## Ticket 007: Monitoring: Detect high-volume login attempts from single IP across distinct usernames

**Sources:** test_scenario slug=high-volume-login-attempts-from-single-ip-across-distinct-usernames-triggers-rate-limit-before-lockout-threshold-is-crossed
**Owner:** Dormouse
**Tier:** fast-follow
**Estimate:** 1-2 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket slug=implement-rate-limiting-on-login-endpoint-per-queen-ruling
- Soft: —

**Description:**

Instrument the /login endpoint to surface a monitoring alert when a single source IP triggers login attempts across more than N distinct usernames within a M-minute window. Alert should fire before the rate-limit blocks the attacker (i.e., at ~1000 attempts, well before 4127). This alert is the early-warning system; the rate-limit is the brake. Tune N and M based on 24 hours of post-mitigation telemetry to avoid false positives from legitimate multi-account access (e.g., support staff, shared office networks).

**Acceptance:**
- Alert fires when single IP attempts >N login failures across >M distinct usernames in <T minutes
- Alert includes source IP, username count, attempt count, and time window
- Alert severity is set to 'high' or higher when pattern matches
- False positive rate <5% when tested against legitimate multi-account access patterns

**Risk:**

N, M, T tuning requires production telemetry; initial thresholds may be too loose (miss attacks) or too tight (false alarms). Plan for one-day calibration cycle after the rate-limit ships.
