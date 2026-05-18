## Ruling 008: Client keystroke buffer must not be trusted for conflict resolution

**GUID:** 01KRXWWPJJM1GXF97C91A8DD1F
**Severity:** high
**Domain:** authentication
**Source:** adr-server-authoritative-note-persistence-with-keystroke-level-localstorage-buffer-and-multi-tab-collision-detection

**Citation:**

OWASP A04:2021 Insecure Design (client-side state as source of truth for authorization decisions); principle of least privilege applied to client-side trust boundaries.

**Finding:**

The keystroke buffer (localStorage) holds ephemeral drafts that may be stale, corrupted, or maliciously modified if the device is compromised or if an attacker gains write access to localStorage. If the collision-detection logic uses the buffered state to make trust decisions ('is my saved version newer than the server's?'), an attacker could manipulate the buffer to convince a client tab that its version is canonical and overwrite a concurrent save from another user session (or another device). The buffer is acceptable as a *recovery mechanism* (survive reload) but not as a *source of truth* for what version should win in a conflict.

**Required Remediation:**

The collision-detection logic must always defer to the server's revision identifier for conflict resolution, never the client's buffered state. When tab A and tab B both attempt to save, the server's comparison of revision identifiers (not the clients' comparison of their buffers) determines which save is canonical. The server's audit trail is the immutable record. Clients use the server's revision ID to detect staleness and warn the user; they do not use the buffer to decide whether a save should proceed.

**Acceptance Criteria:**
- Collision-detection code compares server-provided revision identifiers, not client-side buffered state
- If a client's buffer is stale (revision ID mismatch), the UI warns the user before allowing save
- On save success, the server's returned revision ID overwrites the client's buffer — the buffer is never a source of truth
- Tests verify that a maliciously modified localStorage buffer does not cause a save to proceed without user confirmation

**Residual Risk:**

Single-device loss (laptop stolen) exposes the keystroke buffer's plaintext content. This is accepted for v1 because device-level security (OS disk encryption, device lock) is the expected defense. If the same notebook must support multi-device sync in the future, the audit-trail history and multi-device conflict resolution will require re-assessment.

**Compliance Implications:**

Not applicable to v1 (single-device, single-user, no PII beyond experiment notes).

**Audit Reference:**

This ruling commits the team to a specific trust boundary: server revision IDs are authoritative; client buffers are not. Any future implementation that trusts client-side state for conflict decisions violates this boundary and must be reviewed as a breach.
