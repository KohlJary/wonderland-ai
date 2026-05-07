## Ticket 005: Implement session-count display (today's session count)

**Sources:** review-today-s-session-count
**Owner:** Tweedledee (frontend display) + Tweedledum (count logic)
**Tier:** v1
**Estimate:** 0.5–1 day, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: implement-session-state-backend
- Soft: —

**Description:**

Display a counter on the main screen: "Today: 3 sessions completed" (or similar). Backend tracks completed sessions per day. Frontend fetches the count on app load and updates it whenever a session completes. Hard stop: no week/month/all-time history in v1; no persistent counter across app restart; no date-picker to view other days.

**Acceptance:**
- Backend exposes GET /sessions/today/count returning { "count": N }
- Frontend displays the count on the main screen
- Count increments when a session transitions to 'complete'
- Unit test: backend correctly counts sessions where completion time is today (use faked time)

**Risk:**

Low. This is a simple addition to the session-count endpoint.
