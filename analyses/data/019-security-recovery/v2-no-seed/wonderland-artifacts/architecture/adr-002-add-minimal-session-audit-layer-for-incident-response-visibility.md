# ADR-002: Add minimal session audit layer for incident-response visibility

## Context

The credential-stuffing attack may have resulted in successful authentications against breached accounts. If so, those sessions are now in active use by the attacker. The Queen's ruling (002) requires us to determine what data was accessed during the breach window. The auth service currently issues session tokens but has no audit trail of which sessions accessed which data, and no per-request validation of whether a session is still valid. The Hatter's scenario #2 assumes this visibility exists; it does not.

## Decision

Implement a minimal session-audit layer in auth_service: (1) on successful login, generate a session_id and store it in _incident_store with creation_time and user_id; (2) add a validate_session(session_id) function that checks if the session exists and is not revoked; (3) add a revoke_session(session_id) function for unlock flow; (4) on each data-access request, call validate_session() and log (session_id, endpoint, timestamp) to audit_log. This audit log is what the Queen uses to answer breach-investigation questions. The session_id replaces the current placeholder token_hash.

## Tradeoffs

- In-memory session storage is only safe for the incident-response window (next 2-4 hours). In production, sessions must be persisted and distributed. This is explicitly temporary.
- Per-request session validation on every API call adds latency (~5-10ms per request). Acceptable for incident response; may not be acceptable for production. Future work can optimize with session caches or JWT-based validation.
- Revoking a breached session immediately prevents the attacker from using that session again, but does not prevent them from using the stolen password to create a *new* session. That is why the lockout and rate-limit are also necessary.
- This is not multi-tenancy safe; the audit log does not distinguish which customer's data was accessed. For single-tenant incident response, acceptable. If we ever have multi-tenant architecture, this audit trail will need to be refined.
- If a session is revoked, the legitimate user who owns that account cannot use their old session. They will need to log in again. This is correct — if their credentials were compromised, their old session is compromised too.

## Status

Proposed
