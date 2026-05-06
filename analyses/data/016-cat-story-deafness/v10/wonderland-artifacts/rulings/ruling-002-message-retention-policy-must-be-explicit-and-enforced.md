## Ruling 002: Message retention policy must be explicit and enforced

**Severity:** high
**Domain:** data-handling
**Source:** proposal from Cheshire Cat

**Citation:**

GDPR Article 5(1)(e) (storage limitation); Article 17 (right to erasure). Personal data must not be retained longer than necessary for the purposes for which it was processed. The ADR does not name a retention policy for message content.

**Finding:**

The ADR describes message persistence ('stored in EU-region database') but does not name how long messages are retained. GDPR requires that the team have a lawful basis for retention and a documented policy that enforces that basis. If messages are retained indefinitely, the team cannot satisfy Article 5(1)(e). If messages are deleted on a rolling schedule, the schedule and the mechanism must be explicit and enforceable. Users have a right under Article 17 to request erasure; the system must support that request. None of this is named in the ADR.

**Required Remediation:**

The ADR must specify (a) the retention period for message content (e.g., 'messages deleted 30 days after exchange' or 'messages retained indefinitely; users may request deletion at any time'), (b) the lawful basis for that period (e.g., 'necessary to prevent abuse; older messages pose lower risk'), and (c) the mechanism by which retention is enforced (database TTL, batch deletion job, user-initiated deletion API). This is not implementation detail; it is architectural choice that shapes the data model.

**Acceptance Criteria:**
- ADR revision specifies retention period for messages
- Lawful basis for the period is named (why this period, not shorter or longer)
- Mechanism for enforcement is described (how does the system ensure old messages are actually deleted)

**Residual Risk:**

User-initiated deletion introduces operational complexity (system must track deletion requests, handle partial deletion, manage audit trails). This is acceptable; the alternative (indefinite retention) is not GDPR-compliant.

**Compliance Implications:**

GDPR Article 5(1)(e) (storage limitation principle); Article 17 (right to erasure). This ruling affects the v1 acceptance criteria: the system cannot ship without a documented retention policy.
