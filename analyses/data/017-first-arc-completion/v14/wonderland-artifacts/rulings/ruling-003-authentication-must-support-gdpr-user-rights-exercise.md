## Ruling 003: Authentication must support GDPR user rights exercise

**Severity:** high
**Domain:** authorization
**Source:** proposal (adr: hub-model-translation)

**Citation:**

GDPR Art. 12 (transparency and modalities for exercising user rights); Art. 15 (right of access); Art. 20 (right to data portability); Art. 17 (right to erasure); Art. 21 (right to object). These rights require that the system can authenticate the user making the request and then honor it.

**Finding:**

The Cat's proposal mentions 'basic auth' but does not detail what 'basic' means. For GDPR compliance, the authentication system must be capable of: (1) verifying that the person requesting access to / erasure of / portability of data is the data subject (or their authorized representative); (2) providing audit trails showing when rights requests were made and honored; (3) supporting account deletion, which must trigger cascading deletion of associated data (messages, conversation history, etc.). If the authentication system is minimal (e.g., a bearer token with no session management, no audit trail, no account-deletion support), the application cannot honor GDPR rights requests, and is non-compliant.

**Required Remediation:**

The Tweedles' auth implementation must support: (1) Account identification (email or username, verified on signup); (2) Session management (tokens that can be revoked, sessions that can be terminated); (3) Account deletion endpoint that: triggers full purge of user data (messages they sent, messages directed to them, conversation records, translation logs) according to the retention window specified in the privacy story; generates an audit log entry confirming deletion; executes within a defined SLA (GDPR best practice: within 30 days of the request); (4) Access request endpoint (for Art. 15) that returns all user data in a structured format; (5) Portability endpoint (for Art. 20) that exports data in a machine-readable format (JSON, CSV). Each endpoint must verify the requester's identity and log the request.

**Acceptance Criteria:**
- Auth schema includes user identity (email + verified), session tokens with expiration, and account state (active / deleted)
- Deletion endpoint exists and purges user data from all tables (messages, conversations, auth records)
- Deletion includes audit-log entry naming the user, the deletion time, and the deletion scope
- Access and portability endpoints exist and return user data in machine-readable format
- Test suite confirms deletion actually removes data (not soft-delete) and cascades to related records

**Residual Risk:**

If a user's account is deleted but translations of their messages remain (stored separately for caching or analytics), those translations must also be purged or anonymized. The residual risk is that the team retains translations as a 'technical artifact' and does not consider them user data. They are: under GDPR, once messages are purged, their translations are derived data of those messages and should be purged or anonymized as well. The Tweedles' implementation must be explicit about whether translations are kept separately and, if so, how they are purged when the source messages are deleted.

**Compliance Implications:**

GDPR Art. 12-22 (User Rights); Art. 17 (Erasure); Art. 20 (Portability). These rights are binding; the application cannot ship to EU users without implementing them.

**Audit Reference:**

Ruling: scoping/auth-user-rights. Evidence: auth schema, deletion endpoint code, audit-log table, test coverage of rights-exercise scenarios.
