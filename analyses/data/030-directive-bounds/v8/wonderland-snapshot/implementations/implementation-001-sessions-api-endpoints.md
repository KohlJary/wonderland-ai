## Implementation 001: Sessions API endpoints

**Side:** backend
**Ticket:** feature-001
**Contract:** contract-001: /api/sessions endpoints. Request/response via SessionState model. X-Session-ID header required. State enum: running|paused|completed. Phase enum: focus|break. Returns 400 for invalid durations, 409 for invalid state transitions, 404 when no session exists.
**Ready for review:** yes

**Approach:**

Transient in-memory state store for active sessions keyed by session_id. POST /api/sessions/start creates session with duration validation (1-999 min). GET /api/sessions/current polls session state. POST /api/sessions/current/pause|resume|complete manage lifecycle. Sessions are written to DB on completion.

**Invariants Enforced:**
- Session ID is required (X-Session-ID header); reject if empty
- Focus duration is 1-999 minutes; break duration is 0-999; reject out-of-range
- Session state machine: running→paused→running, or running→paused→completed (reject invalid transitions)
- Each session_id has at most one active (in-memory) session; starting overwrites prior session
- Completed sessions written to DB exactly once per completion

**Schema Changes:**

No migrations; using existing Settings and Session models. Sessions table keyed on session_id + ID; auto-increment primary key.

**Failure Modes Handled:**
- Missing X-Session-ID header → 400
- Invalid duration (≤0 or >999) → 400 with descriptive error
- Pause/resume/complete on wrong state → 409 with state context
- Complete while running → 409 'timer still running'
- No active session for get/pause/resume → 404

**Files:**
- src/backend/api/sessions.py: Complete session management endpoints
- src/backend/api/__init__.py: Included sessions_router in api_router

**Known Limitations:**
- Timer advancement is not implemented (elapsed_time stays 0) — Hatter's xfail tests acknowledge this
- Phase transitions (focus→break) require backend timer, deferred to v2
- Session completion requires external trigger (frontend manual skip or timer), currently must be paused then completed
