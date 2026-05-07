## Contract Note 005: Feature 004: Settings persistence and change propagation

**State:** respond
**Contract Version:** (unlocked)

**Current Shape:**

Backend: Settings table (id, focus_session_length_minutes, break_length_minutes). Endpoints: GET /api/settings (returns current Settings doc), POST /api/settings (accepts {focus_session_length_minutes, break_length_minutes}, upserts, returns updated doc).

**Your Questions (Tweedledum):**

1. **Validation ranges (min/max)?** → Yes, backend should validate:
   - focus_session_length_minutes: >= 1, <= 120 (sanity bounds)
   - break_length_minutes: >= 1, <= 60
   - POST returns `{"status": "success", "settings": {...}}` on success or `{"status": "error", "message": "...", "errors": {"field": "reason"}}` on validation failure
   - Frontend will handle validation errors and show user-friendly message

2. **WebSocket event on Settings write?** → Not for v1. Single-client only. No event emission. If multi-device arrives in future, we can add a WebSocket event and frontend can subscribe to it, but don't include it now.

3. **Return current-session-effective settings or just saved settings?** → Just saved settings. Simpler contract. Session already captured its settings at creation time (snapshot), so no need to return session-specific values. GET /api/settings returns the user's saved preferences only.

4. **Default Settings on first GET?** → Yes. Backend should idempotently create defaults if none exist: focus=25 minutes, break=5 minutes. So GET /api/settings always returns something (never 404). First GET after app install will trigger the default create, then all subsequent GETs return those defaults (or user's customizations).

**Frontend Impact (Tweedledee):**

Frontend provides a settings screen with two number inputs (focus session length, break length) in minutes. On app startup, fetch GET /api/settings and populate inputs. User edits values, presses Save, which sends POST /api/settings with the new values.

Client-side state: Settings are cached in-memory after initial fetch. On save, optimistically update the local cache and show "Saving..." spinner. After POST succeeds, show brief "Saved" checkmark (1-2s), then hide. On POST failure, show error message and disable auto-dismiss of the error state (user must acknowledge or retry).

UI states:
- `loading`: settings are fetching, show skeleton, disable inputs
- `loaded`: inputs enabled, show current values
- `saving`: POST in flight, show spinner next to Save button, disable inputs
- `saved`: briefly show checkmark, auto-dismiss after 1-2s, re-enable inputs
- `error`: POST failed, show error message, enable Retry button

Settings apply to *next* session: if user is mid-session when changing settings, the current session's lengths don't change. Next session created will use the new Settings. This is implemented on the backend (Session snapshots settings at creation time).

Caching strategy: fetch once on app startup. If user navigates away from settings screen and back, use cached values (no refetch). On successful save, use the POST response to update cache. If app is backgrounded for >30 minutes, consider cache stale and refetch on return-to-foreground (to pick up any settings changes from other clients in future multi-device mode, but v1 won't have that).

**Backend Impact (Tweedledum):**

- Settings table: id, focus_session_length_minutes, break_length_minutes
- GET /api/settings: returns `{"focus_session_length_minutes": 25, "break_length_minutes": 5}`, creates defaults if none exist (idempotent)
- POST /api/settings: upserts, validates ranges, returns updated Settings doc or validation errors
- No schema migrations after Feature 001/002 are in place
- No WebSocket events

**Resolution:**

Locked at:
- GET /api/settings: returns current or default Settings (idempotent create on first fetch)
- POST /api/settings: validates focus [1-120], break [1-60], upserts, returns updated doc or error
- No multi-client events (v1)
- Session snapshots settings at creation time (not retroactive to running session)
- Frontend: cache on startup, optimistic update on save, error handling with retry
