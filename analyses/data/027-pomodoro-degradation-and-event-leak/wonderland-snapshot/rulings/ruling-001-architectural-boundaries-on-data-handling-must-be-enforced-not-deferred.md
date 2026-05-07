## Ruling 001: Architectural boundaries on data handling must be enforced, not deferred

**Severity:** high
**Domain:** data-handling
**Source:** adr slug=client-first-architecture-with-server-abstraction-for-multi-user-migration

**Citation:**

GDPR Art. 25 (Data Protection by Design and Default) — architectural decisions about data residency, access controls, and retention are foundational to compliance and cannot be embedded implicitly; they must be explicit design choices. CWE-434 (Unrestricted Upload of File with Dangerous Type) and similar input-boundary issues are easier to avoid when architectural boundaries are real, not aspirational.

**Finding:**

The ADR proposes a server-shaped abstraction without naming which side of the boundary persistence, authentication, and data migration live on in M1. If this creates a situation where M1 code could be extended into multi-user without a clear architectural seam, compliance properties (data residency, access control, retention) become implicit rather than designed. This violates GDPR Art. 25's requirement for Data Protection by Design. It also creates a common failure mode: M1 code 'temporarily' becomes production multi-user code, and the boundaries you deferred are never revisited because re-examining them would require rewriting code that is now live.

**Required Remediation:**

The ADR must explicitly name the three boundary decisions (persistence location, authentication assumption, data migration) as *deferred* and constrain that deferral by requiring M1 implementation to enforce client-only constraints architecturally. This means: (1) no server-side code in M1's persistence layer, (2) no auth-layer code in M1, (3) no multi-user reconciliation logic in M1. The abstraction boundary must be real enough that porting to server-side in M2 requires new code, not refactoring of existing code. This preserves your architectural deferral while making it safe: M1 is genuinely client-only, and M2 boundary decisions are genuine open questions, not hidden choices.

**Acceptance Criteria:**
- ADR explicitly lists the three deferred boundaries under 'Deferred Architectural Decisions' section
- ADR states: 'M1 implementation will enforce client-only constraints architecturally; porting to server-side persistence in M2 will require new code, not refactoring of existing code'
- Caterpillar review of M1 implementation confirms that persistence layer has no server-side code, no auth-layer infrastructure, and no multi-user data-migration logic

**Residual Risk:**

M2 will inherit these boundary decisions; if M2 product scope expands (e.g., 'users want to sync across devices'), compliance requirements may tighten beyond what the architecture assumed. This is acceptable because M2 is genuinely a fresh architectural decision point, not a hidden choice embedded in M1.

**Compliance Implications:**

GDPR Art. 25 (Data Protection by Design) requires that data-handling architecture be explicit and intentional. Deferring boundaries is acceptable; embedding choices as deferrals is not. This ruling enforces the distinction.
