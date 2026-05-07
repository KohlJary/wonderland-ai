## Implementation 005: Session lifecycle with corrected pause duration response

**Side:** backend
**Ticket:** 003
**Contract:** contract-note-003 v1 (Session lifecycle, pause accumulation, atomic SessionRecord write)
**Ready for review:** yes

**Approach:**

Session endpoints enforce state machine (new → running → paused → running → completed). Pause duration is tracked cumulatively in the database (paused_duration_ms). API responses show visible pause duration = stored_duration + current_pause (if session is paused). On resume/complete, the current pause is finalized into paused_duration_ms.

**Invariants Enforced:**
- One running session per user: enforced by query check in start_session
- State machine: running/paused/completed states validated on pause/resume/complete
- Pause duration monotonic: only incremented on resume/complete, never reset
- Session immutability: length and break minutes set at creation, never modified

**Schema Changes:**

None; Session, SessionRecord, Settings tables already created with correct columns (paused_duration_ms, paused_at, status enum, etc.)

**Failure Modes Handled:**
- Invalid state transition (e.g., pause a paused session): 409 Conflict
- Duplicate start attempt (session already running): 409 Conflict
- Session not found: 404
- Pause duration calculation includes in-progress pause, so responses always reflect current state

**Files:**
- src/backend/api/session.py: Added _session_to_response() helper to calculate visible pause duration; endpoints use this helper
- src/backend/models.py: (unchanged; Session/SessionRecord/Settings models already correct)

**Open Questions for Pair:**
- Break sessions: should they be auto-started after completion or explicitly requested by frontend? Contract says explicit, so POST /api/session/start-break needed for Feature 001 full loop.

**Known Limitations:**
- No WebSocket subscription (v1 polls only; future work per contract)
- No break session endpoints yet (/api/session/start-break; breaks must be explicitly started)
- One-running-per-user enforced at application level (safe for single-user v1; future multi-user would add DB constraint)
