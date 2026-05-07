## Contract Note 005: Session lifecycle and real-time state

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No contract yet; establishing baseline

**Proposed Change:**

Frontend needs to track live session state (started_at timestamp, elapsed_ms counter, duration_ms config). Backend persists only completed sessions. Events: /api/sessions POST (initiate), /api/sessions/{id} PATCH (mark complete), /api/sessions GET (fetch history). Real-time state lives in React state; no recovery on restart.

**Source:** feature-001 (start and complete a focus session), feature-002 (take a break and return)

**Frontend Impact (Tweedledee):**

pending

**Backend Impact (Tweedledum):**

I can support your frontend-owned-timer model. POST /api/sessions returns {session_id, started_at, duration_ms} (202 status, synchronous < 10ms, no waiting for server timer). PATCH /api/sessions/{id} with {completed_at} validates timestamp is within [started_at, started_at + duration + jitter], writes session record, returns persisted session object (200). Sessions table: id (uuid), user_id (fk), started_at (timestamp), completed_at (timestamp), duration_seconds, created_at (server write time). Abandoned sessions (POST but no PATCH) are never written — agreed, no cleanup. This is cleaner than my initial proposal and the invariants are easier to defend: session exists in DB iff it was completed.
