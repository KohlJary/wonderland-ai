## Test Scenario 009: Missing session_id handled gracefully (Feature 004)

**Feature:** Use the app without sign-up
**Severity:** high

**Scenario:**

A request arrives at the backend without a session_id header (or empty session_id). The backend either:
- Rejects with 400 Bad Request "session_id required", or
- Auto-generates a new session_id and returns it to the client so they can store it

The contract (CN-003) does not specify which, so this scenario pins the behavior.

**What breaks if this fails:**

Clients lose data if they are not sending session_id, or the backend enters an incoherent state trying to scope data to a null partition.

**Acceptance Criteria:**

- POST /api/sessions/start without session_id returns 400 "session_id is required" (explicit rejection), OR
- POST /api/sessions/start without session_id auto-generates session_id and returns it in response (auto-recovery)
- [Team decision needed on which behavior via contract clarification]
- Either way: no requests are processed without a valid session_id scoping them
