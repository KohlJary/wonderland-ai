## Scenario 002: Successful credential-stuffing attempt against subset of accounts reveals what data was exposed in the upstream breach

**Severity:** silent-wrongness

**Setup:**

Attacker succeeds with 3 credentials out of 2,803 attempts — usernames 'alice@example.com', 'bob@work.org', 'charlie+test@domain.net'. Attack completes and attacker logs in as these three users. System does not detect the breach-credential match.

**Trigger:**

Successful login from same attacking IP (203.0.113.42) within the credential-stuffing window. No detection that this login is part of the attack pattern, not a legitimate user from that IP.

**Expected:**

System flags: (1) login source_ip matches ongoing high-volume attack IP, (2) logs the successful login with 'WARNING: successful auth during active credential-stuffing attack', (3) security team gets alert within 5 minutes. Incident response includes: credential rotation forced for these three accounts, audit log entry created, users notified of compromise.

**Concern:**

Silent success is the dangerous case. If the attacker lands 3 successful logins and the system treats them as normal, no one knows which accounts were exposed. The system detects the *attack* (Dormouse telemetry) but not the *successful compromise within the attack*. Attacker can exfiltrate data for these three accounts before lockout kills the connection.

**Property:**

For all successful logins L where timestamp(L) is within the window of an active credential-stuffing attack from any source_ip, and source_ip(L) matches the attack source_ip: there exists an audit_log_entry marking this login as 'authenticated-during-breach-attempt' with escalation_level=HIGH within 30 seconds of L.

**Implies:**
- Implies Queen ruling: breach disclosure obligations (GDPR, regional law) if successful login count > N
- Implies Tweedle backend: audit logging of logins from attack IPs, correlation with attack detection, escalation trigger
- Implies Cat: review whether successful login to one account + that account's API tokens can be weaponized elsewhere in the system before the account is rotated
