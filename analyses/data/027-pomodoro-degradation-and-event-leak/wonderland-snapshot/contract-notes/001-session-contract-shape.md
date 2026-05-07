# Contract Note: Session API Contract Shape

**State:** proposed
**Thread:** test-scenarios (M4)

## Current Shape
No versioned contract exists yet. Tests in `tests/test_sessions_happy_path.py` and `tests/test_sessions_invariants.py` imply a contract; this note makes it explicit.

## Proposed Contract

### POST /sessions — Create Session
**Request:**
```json
{
  "targetDuration": number,        // minutes, required, must be > 0
  "breakTaken": boolean,           // optional, default false
  "personaTag": string             // optional, for analytics/grouping
}
```

**Response (201 Created):**
```json
{
  "id": string,                    // UUID or similar, server-generated, unique
  "targetDuration": number,
  "breakTaken": boolean,
  "startTime": string,             // ISO 8601 datetime, server-generated at creation
  "createdAt": string,             // ISO 8601 datetime, identical to startTime in M1
  "completionStatus": "pending",   // literal value on creation
  "actualDuration": null,          // null until completion
  "personaTag": string | null
}
```

### PATCH /sessions/{id} — Update Session
**Request:**
```json
{
  "completionStatus": "completed" | "extended",  // state transition
  "actualDuration": number                       // minutes, required on completion
}
```

**Response (200 OK):**
```json
{
  "id": string,
  "targetDuration": number,
  "completionStatus": "completed" | "extended",
  "actualDuration": number,
  "startTime": string,
  "createdAt": string,
  "breakTaken": boolean,
  "personaTag": string | null
}
```

**Error (400 Bad Request) — Invalid Transitions:**
- Reverting completionStatus from completed/extended back to pending
- Setting actualDuration without changing completionStatus
- Negative or zero targetDuration
- Invalid completionStatus value
- actualDuration is allowed to exceed targetDuration (user went overtime)

### GET /sessions — Query Sessions
**Request (query parameters):**
```
GET /sessions?fromDate=YYYY-MM-DD&toDate=YYYY-MM-DD
```

**Response (200 OK):**
```json
[
  {
    "id": string,
    "targetDuration": number,
    "completionStatus": "pending" | "completed" | "extended",
    "actualDuration": number | null,
    "startTime": string,
    "createdAt": string,
    "breakTaken": boolean,
    "personaTag": string | null
  }
]
```

**Behavior:**
- Date boundaries are **inclusive-inclusive** (fromDate 2025-01-01 to 2025-01-01 includes all sessions from that day)
- If fromDate > toDate, return empty list (not an error, per test convention)
- Missing date parameters: backend decision required (error vs. default to last 30 days / today)

### GET /sessions/{id} — Fetch Single Session
**Request:**
```
GET /sessions/{id}
```

**Response (200 OK):**
Same shape as POST response.

**Response (404 Not Found):**
If session ID does not exist.

---

## Frontend Impact

**Client State Required:**
- Session ID mapping (id → session record) for current session + session list
- Timer state (elapsed minutes) — lives in client, reconciles with actualDuration on completion
- UI state machine (loading → viewing → timer-running → completion-pending → synced)

**API Assumptions:**
1. Session IDs are unique and server-generated; frontend never creates an ID
2. startTime is server-generated; frontend does not send it
3. startTime and createdAt are identical in M1 (may diverge in future)
4. Queries return sessions in some order (tests assume list; no specified order yet)
5. Error responses are always `{"detail": "error message"}` (confirm with backend)

**Contracts Not Yet Addressed (pending your response):**
- Do we need an endpoint to fetch app state (language pairs, thread list, viewport) separately from session? Or does it live in a session field?
- Kenji's story (mid-session language pair change) implies either: (a) app settings stored server-side, OR (b) local client state that syncs back. Which?
- Jamie's story (reopen hours later) requires client-state persistence across app close. Is this local device storage (IndexedDB) or server-side? Where is the contract boundary?

---

## Backend Impact
*[Tweedledum fills in]*

---

## Resolution
**Status:** proposed  
**Next step:** Tweedledum responds with:
1. Backend impact assessment
2. Clarification on app-state contract (separate from session, or part of it?)
3. Clarification on error response shape (always `detail`?)
4. Decision on missing date parameters (error or default?)
5. Any schema/timing notes I missed in the tests

Once both sides are filled in, mark `state=agreed` and this becomes the enforced contract for M5 implementation.
