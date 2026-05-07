## Contract Note 002: Settings persistence: focus and break durations

**State:** proposed_backend_response
**Contract Version:** v1 (proposed)

**Current Shape:**

no existing shape

**Proposed Change:**

Frontend settings UI sends 'update-settings' with focus_minutes and break_minutes integers. Backend persists to settings table (user_id nullable for now since single-user, columns: focus_minutes int, break_minutes int, updated_at timestamp). Backend returns full settings object. Frontend caches settings in state and applies as defaults on next session start.

**Source:** Feature 002: Customize session and break lengths

**Frontend Impact (Tweedledee):**

On app load, frontend calls GET /settings, caches result in React state (setSettings hook). Settings UI exposes focus_minutes and break_minutes inputs, sends POST /settings on change. On success, updates local cache; on failure, shows error and reverts inputs to cached value. New session defaults to cached settings; user can override per-session via the start-session dialog. Settings cache is in-memory (lost on page refresh) — frontend re-fetches on load. For v1, no optimistic updates; wait for backend success before updating UI.

**Backend Impact (Tweedledum):**

Backend maintains a settings table, scoped by session_id (see CN-003 for session_id scoping), with columns: {session_id (PK), focus_minutes int, break_minutes int, updated_at timestamp}.

**Endpoints:**
- `GET /api/settings` — returns current settings for the session_id. If no settings row exists for this session_id, auto-create with defaults {focus_minutes=25, break_minutes=5}, return the defaults. Never 404.
- `POST /api/settings` — accepts {focus_minutes int, break_minutes int}, validates both are integers in range [1, 999], persists to settings table (upsert by session_id), returns {focus_minutes, break_minutes, updated_at}.

**Validation rules:**
- focus_minutes must be an integer, ≥ 1, ≤ 999. If not, return 400 or 422 with error detail including the field name.
- break_minutes must be an integer, ≥ 1, ≤ 999. If not, return 400 or 422 with error detail including the field name.
- Both fields are required in POST request body. If either is missing, return 422.
- Non-integer values (strings, floats, null) are rejected as 422.

**Persistence semantics:**
- Settings are upsert by session_id: if a row exists, update it; if not, create it.
- Multiple calls to POST /api/settings with the same session_id overwrite the previous row (no versioning, no history, just latest state).
- updated_at is set to current server time on every POST, not the client time.

**Failure modes handled:**
- Invalid duration (e.g., 0, negative, >999): reject with 400/422 and preserve existing settings (no partial update).
- Missing required field: reject with 422.
- Type mismatch (string instead of int): reject with 422.
- On validation error, settings table row is untouched (atomic: either full success or no change).

**Defaults:** If GET /api/settings is called before any POST (fresh session_id), auto-create row with {focus_minutes=25, break_minutes=5}. This is implicit row creation; Tweedledee's code assumes this behavior (he fetches settings on app load without ever setting them).

**Invariant enforced:**
- Every session_id has exactly one settings row (or zero, until first GET, then exactly one).
- A settings row's focus_minutes and break_minutes always satisfy the validation rules.

**Concern:** The proposal assumes auto-creation of default settings on first GET. This is a convenience for single-user, but in multi-user it means the backend auto-creates rows for every session_id that ever calls GET /api/settings, even if they never update it. This could be a lot of rows. For v1 it's fine; note it as a stretch-goal optimization (lazy deletion of unused rows, or garbage collection of never-updated defaults).

**Integrates with CN-001:** When POST /api/sessions/start is called without focus_minutes/break_minutes, the backend checks if GET /api/settings would return custom values, and uses those as the session defaults. If GET /api/settings returns the auto-created defaults (25/5), those are used.

**Ready to mark agreed:** yes, this is clear and testable.
