## Ruling 007: Audit trail must capture full note state at each save; no delta-only encoding

**GUID:** 01KRXWW3ZS79JPT6AKHTSVVXBY
**Severity:** high
**Domain:** logging-and-audit
**Source:** architectural-decision-pending-from-cat-adr

**Citation:**

OWASP A09:2021 Logging and Monitoring Failures; SOC 2 CC7.2 System Monitoring; GDPR Art. 32 (audit trail for accountability).

**Finding:**

The prior audit-trail ruling commits to capturing saved states so the system can defend what happened and when. If the implementation captures only deltas (changes between saves), reconstruction of a note's state at any point in time requires replaying all prior deltas — a complexity that makes forensic investigation, incident response, and compliance demonstration unnecessarily expensive. Deltas alone are also ambiguous: if a user saves a note with the same body twice (changing only tags), a delta-only log would show nothing changed, hiding the save event itself. The audit trail would be incomplete. Full snapshots are more expensive in storage but forensically complete and unambiguous.

**Required Remediation:**

The audit-trail schema must capture the complete note state (title, body, tags) at each save event, not deltas. The schema should store: {save_id, note_id, title, body, tags, saved_at, saved_by (user/session), previous_state_hash (for change detection if needed)}. Deltas can be computed from snapshots if needed; the reverse is not possible.

**Acceptance Criteria:**
- Each note save produces an immutable audit-trail entry containing the full note state (title, body, tag list) at that moment
- The entry includes a timestamp (saved_at) and a hash or version identifier linking to the prior state
- The audit trail is queryable by note_id and timestamp to reconstruct the note's state at any point in history
- Tests verify that a note edited twice with different bodies produces two distinct audit entries, not one delta

**Residual Risk:**

Storage cost grows linearly with save frequency. For a user with 100 notes saved 10 times each, the audit table will have 1000 entries. At ~2KB per entry (title + body + metadata), this is ~2MB per user. Acceptable for single-user v1; may require partitioning or archival in fast-follow if the app scales to multi-user.

**Compliance Implications:**

GDPR Art. 5(1)(f) requires 'integrity and confidentiality; […] in a manner that ensures appropriate security of the personal data.' An audit trail that cannot reconstruct state at a given time is not a credible integrity defense. Full snapshots make the audit trail a source of truth for 'what did the user have at time T'; deltas make it a source of confusion. Regulators will prefer snapshots.

**Audit Reference:**

Audit entry schema locked. Tweedles must implement per this specification. Future audit-trail queries (export for regulator, show note history to user) depend on this structure being complete and immutable.
