## Contract Note 007: Session duration configuration: GET/PATCH defaults

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

undefined

**Proposed Change:**

Define GET /config (returns user's session_length_minutes, break_length_minutes defaults). Define PATCH /config (accepts {session_length_minutes, break_length_minutes}, persists, returns updated config). When user starts a session, backend uses their configured default unless overridden.

**Source:** Feature 005.

**Frontend Impact (Tweedledee):**

On app load, fetch /config and cache in client state. Display in settings UI. On change, PATCH /config, update cache, reflect in UI immediately (optimistic). If PATCH fails, revert cache + show error.

**Backend Impact (Tweedledum):**

User config table: user_id (FK), session_length_minutes (default 25, range 1–120), break_length_minutes (default 5, range 1–60), timezone (default 'UTC'), created_at, updated_at. GET /config returns {session_length_minutes, break_length_minutes, timezone}. PATCH /config accepts {session_length_minutes?, break_length_minutes?, timezone?}, validates ranges, returns 200 with updated config. Invariant: valid ranges enforced at DB constraint level. When POST /sessions/start is called, backend reads user's session_length_minutes and uses it as target_duration_seconds (convert minutes→seconds). Can be overridden per-session in v1.1; for v1, always use config default.
