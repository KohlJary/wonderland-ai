## Ruling 013: Successful-login observability during attack window — required for breach-notification determination

**Severity:** high
**Domain:** logging-and-audit
**Source:** Alice user-consequence concern + Queen breach-notification ruling #2

**Citation:**

GDPR Art. 33 (breach notification: controller must notify supervisory authority without undue delay); state breach-notification laws (e.g., CA AB 375, NY 23-GDPC); incident-response requirement: cannot determine which accounts to notify without knowing which login attempts succeeded

**Finding:**

The Queen's ruling on breach-notification obligations requires the team to determine which accounts experienced successful credential compromise during the attack window. The current implementation tracks failed login attempts and lockouts, but has zero observability into *successful* authentications during the attack. If an attacker obtained valid credentials and logged in at 14:47 UTC, the system will not emit any observable event marking this as a successful-login-during-attack. The team will ship a ruling they cannot execute, and affected users will remain unnotified of compromise. This is a user harm: compromised credentials go undetected, and the account remains at risk.

**Required Remediation:**

The Tweedles will instrument successful-login events with timing information that allows post-incident correlation with the attack window. The observability contract (ruled above) must specify: (1) successful-login event is emitted on every authentication success, (2) event includes timestamp (for attack-window correlation), user identifier (for breach-notification determination), and client context (IP, User-Agent, for forensics). The Dormouse will ensure these events are queryable post-incident without log parsing or manual correlation. Before v1 ships, there must be a working query: "show me all successful logins on these email addresses between [attack-window-start] and [attack-window-end]," so the breach-notification work (Alice's concern) can execute cleanly.

**Acceptance Criteria:**
- Successful-login events are emitted and observable in production telemetry during normal operation
- Events include timestamp, user identifier, and client context (IP, User-Agent)
- Dormouse can query successful-login events for a specific email address within a specific time window, post-incident, within [1 minute] of query submission
- Post-incident test: after a simulated credential-stuffing attack with N successful logins injected, the Dormouse can identify all N successful logins without manual log inspection
- Breach-notification ticket references the successful-login query as its foundation

**Residual Risk:**

If an attacker used stolen credentials before the rate-limiting implementation was deployed, those successful logins may not be in telemetry (if logging was not enabled for auth events prior to the incident). The team will do forensic recovery from available logs; this is acceptable. Going forward, observability of successful logins is mandatory.

**Compliance Implications:**

GDPR Art. 33 and state breach-notification laws require the controller to notify affected individuals of confirmed compromise. Without observability of successful logins during the attack, confirmed compromise cannot be determined, and the legal obligation cannot be satisfied. The successful-login observability is a compliance control, not optional instrumentation.

**Audit Reference:**

Successful-login event specification (part of observability contract); production telemetry query results; breach-notification ticket (founded on this query)
