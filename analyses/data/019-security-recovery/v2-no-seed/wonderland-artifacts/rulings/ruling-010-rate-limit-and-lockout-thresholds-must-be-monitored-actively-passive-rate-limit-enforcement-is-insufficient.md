## Ruling 010: Rate-limit and lockout thresholds must be monitored actively; passive rate-limit enforcement is insufficient

**Severity:** high
**Domain:** logging-and-audit
**Source:** test_scenario from Mad Hatter; incident-response observation from Dormouse

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; CWE-307 Improper Restriction of Rendered UI Layers or Frames; incident baseline: 12±4 failed login attempts/minute under normal load, spike to 4,127 in 8 minutes is 343x baseline and undetectable without active monitoring.

**Finding:**

The rate-limit and lockout enforcement shipped by Tweedledum are reactive — they stop the attack *after* it starts (once threshold is crossed). The Dormouse's telemetry detected the spike retrospectively; legitimate users were already locked out by the time mitigation awareness reached the team. This attack will recur (same attacker, different credentials list; different attacker, same vector), and passive enforcement means 47 more users locked out before detection next time. The Hatter's scenario #1 exposes the race: rate-limit must trigger before lockout threshold is crossed, but if rate-limit response is not *monitored*, the team does not know it triggered until the spike is already large.

**Required Remediation:**

Implement three active monitoring checks on the /login endpoint: (1) alert when failed-login rate exceeds baseline+3σ (baseline 12±4, alert at 25+/minute), (2) alert when lockout-event rate exceeds baseline (lockout baseline is ~0; alert at 5+/minute), (3) circuit-break and page-on-call when either alert fires. These checks must be live and armed *before* the rate-limit code is merged to production. Passive rate-limiting stops the attack; active monitoring stops the *next* attack before users are locked out.

**Acceptance Criteria:**
- Alert fires within 60 seconds of failed-login rate exceeding 25/minute (real-world test: curl -based credential-stuffing simulation against staging)
- Alert includes both the raw rate (N failures/min) and the baseline deviation (N/baseline ratio) so on-call can assess severity immediately
- Circuit-break is armed and tested: when alert fires, new /login requests return 429 (rate-limited) instead of 401 (auth-failed)
- On-call page-load is tested and includes a runbook for 'active credential-stuffing in progress' with next steps (rate-limit threshold adjustment, breach investigation initiation, user notification decision)

**Residual Risk:**

Active monitoring detects credential-stuffing attacks after 5-10 minutes of sustained attempt (alert latency + on-call response time). In that window, the attacker can lock 10-20 legitimate users if the rate-limit threshold is not aggressively set. This is acceptable; the alternative (pre-detection hardening via CAPTCHA, MFA, etc.) is out of scope for incident response and belongs in the threat-model update (ruling 003). The residual risk is documented and reviewed quarterly against attack-recurrence data.

**Compliance Implications:**

GDPR Art. 32 (security of processing) and Art. 33 (breach notification) both require that systems demonstrate timely detection of unauthorized access attempts. Passive rate-limiting is enforcement; active monitoring is the evidence that enforcement worked. The audit trail must record not just what the rate-limit did, but when and why it was triggered.

**Audit Reference:**

Threat Garden entry: 'Credential-stuffing attack (IP-based) / Active detection gap / First identified: thread 47 (this thread) / Mitigation: rate-limit + lockout (v1 incident response) / Detection hardening: active monitoring thresholds (v1.1 post-incident) / Status: mitigated, pending monitoring deployment.'
