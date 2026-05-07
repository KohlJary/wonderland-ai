## Ticket 006: Frontend timer UI and session rendering

**Sources:** story:start-and-complete-a-focus-session, story:take-and-track-a-break
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1.5–2 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket:define-session-state-machine-and-contract-for-timer-history-seam, ticket:timer-state-machine-and-session-lifecycle
- Soft: ticket:settings-read-and-write-endpoints

**Description:**

Timer screen: large countdown display (mm:ss), current session type (Focus / Break), buttons (Start, Pause, Resume, Complete). Poll GET /session every second for state. On session completion (received from backend), show completion badge and auto-start next session type (focus → break, break → focus) or return to idle. Handle app background/foreground (pause polling when backgrounded; resume on foreground or wall-clock time elapsed).

**Acceptance:**
- Timer displays mm:ss countdown from backend state
- Start button calls POST /session, displays session_id, starts polling
- Pause button calls PATCH /session?action=pause, freezes display
- Resume button calls PATCH /session?action=resume, unfreezes
- On session completion (GET /session returns completed state), show badge, auto-start next type after 1s
- App backgrounding pauses polling; foregrounding resumes (or uses wall-clock time to reconcile)
- Settings button navigates to settings screen

**Risk:**

Polling is crude; if poll misses a completion, UI gets out of sync with backend. Upgrade to websockets or server-sent events in fast-follow if needed. For v1, use settings-configurable poll interval (default 1s) so it's tunable if needed.
