## Ruling 009: Audit trail must be immutable and complete enough for forensic reconstruction

**GUID:** 01KRXX70J94H4EXR08TRVV48DF
**Severity:** high
**Domain:** logging-and-audit
**Source:** adr-server-authoritative-note-persistence-with-keystroke-level-localstorage-buffer-and-multi-tab-collision-detection

**Citation:**

CWE-1275 (Undefined Behavior Related to Undefined Control Flow); OWASP A09:2021 Logging and Monitoring Failures (logging must support forensic reconstruction of user actions)

**Finding:**

The audit trail is the system's defense against 'I didn't change that note' disputes and is the basis for incident reconstruction. If the log is incomplete or ambiguous (deltas without full reconstruction logic, or snapshots without sufficient timestamp/ordering precision), the system cannot credibly answer 'what was this note's state at time T?' and cannot reconstruct what a user actually did. This is both a security problem (forensic blindness) and a compliance problem (audit trail that doesn't actually audit).

**Required Remediation:**

Every note write to the backend must generate an immutable log entry that includes: (1) timestamp with sufficient precision to order events (millisecond minimum), (2) user identity (for v1, implicitly single-user, but the field must exist and be populated so it doesn't become a future bypass), (3) the complete saved state at that moment (title, body, tags, revision identifier), (4) hash or signature of that state to detect tampering. The log entry must be written atomically with the note update so that no write succeeds without a corresponding log entry. The log must not be updatable or deletable by the application — it is append-only.

**Acceptance Criteria:**
- Every note saved to the backend produces an audit-log entry with timestamp, user_id, full saved state (title, body, tags, revision_id), and state_hash
- Audit log is append-only (no UPDATE or DELETE on the log table itself; only INSERT)
- Timestamps are millisecond-precision and can be used to reconstruct note state at any point in time
- If a write fails (database error, network error), the log entry is not created; if the log entry fails, the note write rolls back
- The system can answer 'what was this note at time T?' by selecting the log entry with the highest timestamp <= T

**Residual Risk:**

The schema choice (full snapshot vs. delta) affects query performance and storage cost, not audit completeness. Full snapshots are simpler and faster to reconstruct; delta logs are more compact but require replay logic that could fail. Both are acceptable if they meet the acceptance criteria above. The Cat should choose based on storage and query performance tradeoffs, but the audit requirement is non-negotiable regardless of which representation is chosen.

**Compliance Implications:**

Audit trails are required by most compliance frameworks (GDPR Art. 32, HIPAA, SOC 2). An incomplete audit trail is a finding. The log must exist, must be immutable, and must be complete enough that a regulator can see what happened when. 'We can't reconstruct past state' is not a defensible position.

**Audit Reference:**

This ruling enforces the audit-trail requirement from the multi-tab collision-detection ruling and the server-authoritative architecture. The audit log is the system's ground truth about what was persisted; revisions identifiers (opaque hashes) are client-side mechanism to detect collision; the audit log is the server-side record of what actually happened.
