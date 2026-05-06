## Ticket 008: Monitoring: Detect User-Agent rotation as a rate-limit bypass signal

**Sources:** test_scenario slug=attacker-rotates-user-agent-strings-to-bypass-any-rate-limit-keyed-only-on-ip-user-agent-combo
**Owner:** Dormouse
**Tier:** fast-follow
**Estimate:** 1.5-2.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket slug=implement-rate-limiting-on-login-endpoint-per-queen-ruling
- Soft: —

**Description:**

The rate-limit in the immediate mitigation is keyed on source IP (per the Queen's ruling). An attacker rotating User-Agent strings can stay within the per-IP rate-limit while maintaining high overall volume. Surface a monitoring alert when a single source IP makes login attempts with >K distinct User-Agent strings within a M-minute window. Alert should have lower false-positive threshold than the raw high-volume alert (this pattern is more directly indicative of attack). Consider correlation: if high User-Agent rotation + high distinct-username count, severity escalates.

**Acceptance:**
- Alert fires when single IP makes login attempts with >K distinct User-Agent strings in <T minutes
- Alert includes source IP, User-Agent count, distinct-username count (if applicable)
- Correlation with distinct-username count escalates severity when both patterns are present
- False positive rate <2% (this pattern is more attack-specific than raw volume)

**Risk:**

K and T tuning requires telemetry observation. Legitimate scenarios (shared office network, user switching browsers/devices) may trigger false positives; plan for 24-hour post-deployment observation.
