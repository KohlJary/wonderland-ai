## Contract Note 005: Session completion event and backend logging

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

None — v1 negotiation

**Proposed Change:**

When a timer completes (elapsed >= configured duration), frontend POST /sessions/log: { "type": "focus"|"break", "duration_configured_seconds": number, "duration_actual_seconds": number, "completed_at": ISO8601 }. Backend persists; responds { "session_id": string, "acknowledged": true }. Frontend uses session_id for future reference (v2 edit/delete). This is the single source of truth for session history.

**Source:** Feature 001 (focus timer), Feature 002 (break timer + auto-start), Feature 003 (history read-back). Tickets 001, 004, 005.

**Frontend Impact (Tweedledee):**

I drive the countdown locally, emit exactly once per session. I handle success/retry on failures. The completed_at timestamp is generated client-side at completion time. I do NOT persist sessions locally; all history lives on backend.

**Backend Impact (Tweedledum):**

Backend receives POST /sessions/log with { type: 'focus'|'break', duration_configured_seconds: number, duration_actual_seconds: number, completed_at: ISO8601 }. I persist to session_log table with columns: (id PK, user_id FK, type ENUM, duration_configured_seconds INT, duration_actual_seconds INT, completed_at TIMESTAMP, created_at TIMESTAMP). Validates: duration_actual <= duration_configured + 5% (allows timer drift). Handles duplicate POST (idempotency): session_id is deterministic from (user_id, completed_at, type) hash, or I generate UUID on first arrival and require client to resend same UUID for retries. Responds { session_id: string, acknowledged: true, timestamp: ISO8601 } with 200 OK. 4xx on validation; 5xx on persistence failure (client retries). No transactions needed; single insert is atomic.
