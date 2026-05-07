## Implementation 001: Session lifecycle models and POST /sessions endpoint

**Side:** backend
**Ticket:** feature-001
**Contract:** session-state-envelope-and-lifecycle v1 (agreed M3); session_completion_event_shape v1 (agreed M3)
**Ready for review:** no

**Approach:**

Session model with state machine (created → active → completed); POST /sessions creates and returns session_id; idempotent on repeated calls within same second (prevents double-create on network retry). Session state persisted to database with timestamp tracking.

**Files:**
- src/backend/models.py: Session model with fields (id, user_id, created_at, started_at, completed_at, duration_seconds, break_duration_seconds, state)
- src/backend/api/sessions.py: POST /sessions, GET /sessions/{id}, POST /sessions/{id}/complete endpoints

**Open Questions for Pair:**
- Frontend expects session_id in POST /sessions response — confirming response envelope is {session_id, created_at, state}?
- Break timing: does frontend track break duration client-side, or does it hit POST /sessions/{id}/complete with break_duration in the body?

**Known Limitations:**
- Idempotency window is 1 second (arbitrary choice pending frontend request patterns); may need tuning
- No distributed lock on concurrent session creation for same user — relies on database UNIQUE constraint; acceptable for MVP
- Session state transitions not yet validated (created→active, active→completed) — Caterpillar will flag
