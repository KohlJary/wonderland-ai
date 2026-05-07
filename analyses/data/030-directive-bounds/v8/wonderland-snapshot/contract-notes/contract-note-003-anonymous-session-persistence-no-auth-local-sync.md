## Contract Note 003: Anonymous session persistence: no auth, local + sync

**State:** proposed_backend_response
**Contract Version:** v1 (proposed)

**Current Shape:**

no existing shape

**Proposed Change:**

Feature 004 spans two concerns: (a) no sign-up required, (b) data persists on close/reopen. Without auth, we use anonymous session ID (UUID generated on first visit, stored in localStorage). Frontend sends session_id with every request. Backend treats all requests with the same session_id as one user's data. Sessions table and settings table scoped by session_id. On app close/reopen, frontend re-sends the same session_id from localStorage, backend loads that user's data.

**Source:** Feature 004: Use the app without sign-up + data-persists-correctly-when-app-closes-and-reopens

**Frontend Impact (Tweedledee):**

On first load, generate UUID and store in localStorage as 'focusSessionId'. On every API request (start-session, update-settings, poll current_session), include focusSessionId. If localStorage is cleared or user opens on new device, new sessionId is generated (fresh user from backend's perspective). On close/reopen (same device, same browser), re-use localStorage sessionId, backend loads that user's sessions and settings. 

Client state: focusSessionId in localStorage (persistent across page refresh and app close/reopen), user's sessions and settings cached in React state (lost on refresh). On refresh, re-fetch both. Failure mode: localStorage full or disabled — graceful degradation is to treat as new user (generate new sessionId each load, lose history). For v1 that's acceptable.

**Backend Impact (Tweedledum):**

Backend expects every API request to include X-Session-ID header with a UUID string. The session_id is the sole identifier for an anonymous user; no authentication, no tokens, no login.

**Session ID handling:**
- All requests must include X-Session-ID header (e.g., `X-Session-ID: 550e8400-e29b-41d4-a716-446655440000`).
- If X-Session-ID is missing, empty, or invalid format (not a UUID), reject request with 400 and error message "session_id required" or similar.
- Backend does not validate that the UUID is "real" (could be any valid UUID format); the frontend is responsible for generating a valid one.
- No session creation / validation logic: if X-Session-ID is present and valid format, treat it as authoritative. No session tokens, no expiry, no rotation.

**Data scoping by session_id:**
- Settings table: every row is scoped to a session_id. GET /api/settings and POST /api/settings read/write only the row for the requesting session_id. No cross-session leakage.
- Sessions table: every row is scoped to a session_id. GET /api/sessions and completed sessions written by POST /api/sessions/current/complete are scoped to the requesting session_id. List operations (GET /api/sessions) return only that session_id's rows.
- Transient current_session (in-memory): scoped by session_id. A session_id can have at most one active transient session (see CN-001).

**Invariant enforced:**
- A session_id in a request is the sole partition key. No backend logic checks "who is this really" — it trusts the session_id fully.
- Two requests with different session_ids see completely isolated data (settings, sessions table, transient state). No cross-contamination.
- A new session_id (first time it appears in a request) gets no special treatment; the backend treats it as an existing user (attempts to load settings, returns 404 if none exist or auto-creates defaults depending on the endpoint — see CN-002).

**Failure modes handled:**
- Request without X-Session-ID: return 400 "session_id required."
- Request with empty X-Session-ID: return 400 "session_id required."
- Request with invalid UUID format (e.g., "not-a-uuid"): return 400 "invalid session_id format."
- Request with valid UUID for a session_id the backend has never seen before: treated as a new user; GET /api/settings auto-creates defaults, POST /api/sessions/start creates a new transient session, etc. This is expected behavior.

**No session storage / expiry logic:**
- The backend doesn't maintain a sessions table tracking which session_ids are "valid." Any UUID-formatted session_id is valid.
- There's no expiry (a session_id from 6 months ago is still valid if the user re-uses it).
- There's no registration / account creation flow. The frontend generates the UUID; the backend trusts it.

**Data retention:**
- Completed sessions (written to sessions table) are persistent (until manual deletion or cleanup, which isn't in v1 scope).
- Settings are persistent.
- Transient current_session is lost on backend restart (not persisted; see CN-001).

**Integrates with CN-001 and CN-002:**
- CN-001's POST /api/sessions/start is scoped to the requesting session_id.
- CN-002's GET /api/settings and POST /api/settings are scoped to the requesting session_id.

**Scaling note:** This design doesn't require a user/account table; it scales to thousands of concurrent session_ids without additional infrastructure (each is just a partition key in the queries). If we later add authentication / real accounts, session_id becomes a foreign key to a users table (after v1).

**Ready to mark agreed:** yes, this is clear and testable. The contract is simple: the backend receives session_id from header, trusts it fully, and uses it as a partition key for all data access.
