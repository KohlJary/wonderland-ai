## Contract Note 005: User preferences & duration customization

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

N/A — proposing initial contract

**Proposed Change:**

Settings entity keyed to user_id (singleton per user in v1). Fields: session_duration_minutes (default: 25), break_duration_minutes (default: 5). API endpoint /settings returns {session_duration_minutes, break_duration_minutes}. Endpoint PATCH /settings accepts {session_duration_minutes?, break_duration_minutes?} and persists. New sessions started after PATCH use updated defaults. Existing active session is NOT retroactively affected. Changes take effect on next session.

**Source:** Feature 005 (customize durations); ticket 013

**Frontend Impact (Tweedledee):**

Client fetches /settings on app launch and caches indefinitely (or until user edits). Settings form displays current values; user edits trigger optimistic client-state update + PATCH request. On PATCH response (success), cache updates. On PATCH error, client rolls back form to last-known-good server state + error message.

Client state: {settings: {session_duration_minutes, break_duration_minutes}, settingsForm: {session_duration_minutes, break_duration_minutes, isDirty, isSaving}}. Form state separate from canonical settings to enable undo on error.

UI states: loaded (displaying form with current values), saving (user tapped save, awaiting PATCH response), error-recoverable (PATCH failed, form reverted, user can retry). Validation (client-side): both duration fields must be integers, 1–180 minutes.

User flow: Settings screen → user edits values → taps Save → optimistic update (form disabled, saving indicator) → on success, flash success message + refresh any visible stats. On error, revert form to previous values + show error.

Open questions for pair:
1. Are there server-side validation constraints on min/max duration? (Client needs to know to validate form, avoid sending invalid PATCH.)
2. If user has an active session and changes session_duration_minutes, what happens? (I assume it doesn't affect the current session, only the next one — confirming this avoids UI confusion.)
3. Should PATCH be idempotent? (i.e., POSTing the same settings twice returns success both times?) Assuming yes for robustness.

**Backend Impact (Tweedledum):**

Settings table: user_id PK, session_duration_minutes (default 25), break_duration_minutes (default 5), updated_at UTC. PATCH /settings is upsert. Validation: both fields in [1, 180]; server rejects out-of-range with 400. Session created after PATCH uses updated Settings; active sessions not retroactively affected. PATCH idempotent. GET /settings returns current values; on first launch, return defaults.
