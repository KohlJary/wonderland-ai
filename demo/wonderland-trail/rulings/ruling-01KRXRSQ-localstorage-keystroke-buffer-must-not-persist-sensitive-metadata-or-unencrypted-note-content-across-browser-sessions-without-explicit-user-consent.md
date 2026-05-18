## Ruling 001: localStorage keystroke buffer must not persist sensitive metadata or unencrypted note content across browser sessions without explicit user consent

**GUID:** 01KRXRSQR83W3G0X5FS0V7WZ85
**Severity:** high
**Domain:** data-handling
**Source:** proposal: client-buffered, server-authoritative note persistence

**Citation:**

OWASP A01:2021 Broken Access Control; CWE-521 Weak Password Requirements; client-side storage is accessible to XSS and malicious browser extensions. localStorage persists across sessions without encryption, exposing recovery data to attackers with device access.

**Finding:**

The proposal buffers keystroke state to localStorage to survive page reload. If this buffer accumulates note content, tags, or metadata unencrypted, an attacker with device access (stolen laptop, shared workstation, malware with local read) can recover Kohl's work product and potentially sensitive experimental notes. The buffer is also vulnerable to XSS if the note content is later rendered unsanitized; malicious markdown in a note could exfiltrate the buffer on next edit session.

**Required Remediation:**

1) localStorage buffer must store *only* the keystroke recovery payload (opaque serialized editor state), not plaintext note content or metadata. Content reconstruction must require round-trip from server or re-entry by the user. 2) Before persisting any user input to localStorage, sanitize against script injection — assume the buffer may be read by untrusted code. 3) On application load, purge the keystroke buffer after successful server sync; do not accumulate stale recovery state across sessions. 4) Document to Kohl (in UI or help) that localStorage recovery is session-local and should not be relied on for persistence across devices.

**Acceptance Criteria:**
- localStorage buffer content is opaque to inspection (serialized, not plaintext JSON with note text visible)
- No note title, body, or tag content persists in localStorage after server sync
- XSS attack targeting the keystroke buffer (injected via malicious markdown in a recovered note) does not exfiltrate the buffer to an attacker domain
- Keystroke buffer is cleared after successful server roundtrip or on explicit user logout

**Residual Risk:**

Keystroke buffer may be recovered by forensic disk analysis after device compromise. This is acceptable: the residual risk is the attacker already has device access. The mitigation reduces exposure to logical attacks (XSS, malware with read-only access) and session-local threats (shoulder-surfing, shared workstations). We accept the forensic-analysis vector as inherent to client-side caching.

**Compliance Implications:**

If Kohl's notes contain personal data or experimental data subject to data minimization (GDPR Art. 5), the buffer must not unnecessarily retain copies after sync. The sanitization requirement also supports user data sovereignty: Kohl should be able to inspect/delete what the application stores locally.

**Audit Reference:**

Threat model for localStorage handling in single-user note app; ruling applied to client-buffered, server-authoritative proposal (thread: architecture).
