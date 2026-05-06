## Scenario 012: Successful login during active attack is not distinguished from normal login in observability

**Severity:** silent-wrongness

**Setup:**

Credential-stuffing attack is ongoing (4,000+ attempts/min from 203.0.113.42). On the same minute, one of the attacker's guesses succeeds: the account associated with the stolen credential authenticates successfully.

**Trigger:**

A login attempt that (a) would normally be rate-limited (it's from the attack IP) but (b) succeeds anyway because the credentials are correct, and (c) triggers record_success() to clear the lockout counter.

**Expected:**

Login succeeds and session is created. But an observable event is emitted that distinguishes this login from benign successful logins: (e.g., 'auth.login_success_during_attack_window', tagged with: was_rate_limited_before, failed_attempt_count_before, source_ip_velocity, timestamp). Dormouse can flag: 'this account succeeded while being bombarded from this IP — likely compromised.'

**Concern:**

The current implementation treats a successful login the same way regardless of context. If an attacker successfully authenticates with a stolen credential at 14:47:32 UTC while the attack is in full swing, the system logs the success to the Session table but produces no signal to observability that this might be a breach. The Queen's breach-notification ruling requires knowing 'which accounts were successfully compromised', but the current instrumentation cannot distinguish compromised-via-attack from legitimate-login-during-coincidentally-high-volume.

**Property:**

For all successful logins L during a period of detected attacks, there exists an observable metric or alert-rule threshold that flags logins_where(source_ip in attack_ips OR source_ip_has_high_failure_rate_in_window), enabling post-incident breach analysis.

**Implies:**
- Requires correlation between rate-limit/lockout telemetry and session-success telemetry.
- Dormouse owns the contract for attack-detection signals and cardinality bounds.
