## Ruling 001: Message lifecycle must be session-scoped with explicit user consent

**Severity:** critical
**Domain:** compliance
**Source:** proposal (adr: hub-model-translation)

**Citation:**

GDPR Art. 5(1)(e) (storage limitation); Art. 6 (lawful basis); Art. 7 (consent); GDPR Recital 32 (freely given, specific, informed, and unambiguous consent).

**Finding:**

A chat application processing messages of EU users cannot retain those messages indefinitely without explicit lawful basis. The proposal correctly anchors to explicit user consent as the lawful basis (Art. 6(1)(a)). However, the consent flow must be specific about retention: the user must consent to *how long* messages are kept, not just that they are kept. If messages are session-scoped (i.e., deleted when the conversation ends or after a user-configurable idle period), the user sees a concrete retention promise they can decide for or against. Indefinite retention requires either explicit consent to 'store forever' or a different lawful basis (e.g., legal obligation, contract performance), neither of which is present here.

**Required Remediation:**

Before implementation, Alice's 'user joins from EU and sees privacy consent flow' story must specify: (1) the exact retention window (e.g., 'messages delete 30 days after last activity in the conversation,' or 'messages delete when the user ends the conversation,' or 'user can manually delete conversations and all messages therein'); (2) the lawful basis clearly stated in the consent (e.g., 'We store your messages for 30 days to let you access conversation history; after that, they are permanently deleted'); (3) the user's ability to revoke consent and its effect (does revoking consent trigger immediate deletion of all their messages, or is that a separate user right under Art. 17?). The Tweedles' implementation must enforce this retention window at the database layer — no exceptions, no 'soft deletes' that leave data behind for auditing.

**Acceptance Criteria:**
- Alice's privacy story explicitly names the retention window in user-facing language
- The consent UI surfaces the retention window as a discrete, uncheckable fact (user cannot consent to 'keep forever')
- The consent schema captures explicit user assent to the named retention window
- The database schema includes a message-deletion trigger that fires at the retention window boundary (no manual override)
- The Tweedles' test suite includes scenarios confirming messages are deleted at the boundary (not soft-deleted, actually purged)

**Residual Risk:**

If a user consents to a retention window and then requests deletion before the window expires (invoking Art. 17 right to erasure), the system must honor the earlier request. This is a separate right and is not negotiable. The residual risk is that the team forgets this and treats consent-to-retention as a reason to deny the erasure request. It is not. Rulings on erasure requests will follow once the Tweedles implement Art. 17 handling.

**Compliance Implications:**

GDPR Art. 5 (Data Minimization + Storage Limitation); Art. 6 + Art. 7 (Lawful Basis + Consent); Art. 13/14 (Transparency); Art. 17 (Right to Erasure). This ruling operationalizes all of these. Without session-scoped retention and explicit consent, the application is non-compliant at launch.

**Audit Reference:**

Ruling: scoping/message-lifecycle-retention-consent. Evidence: privacy story artifact, consent schema, database schema, test coverage.
