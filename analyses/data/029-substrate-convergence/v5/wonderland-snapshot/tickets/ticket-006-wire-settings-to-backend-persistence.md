## Ticket 006: Wire settings to backend persistence

**Sources:** customize-session-and-break-lengths
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: wire-timer-state-to-backend-persistence
- Soft: implement-customizable-session-and-break-lengths

**Description:**

Extend the user settings endpoint to store and retrieve custom session/break lengths. When user changes settings on frontend, POST the new values to backend. On app load, fetch and apply saved settings.

**Acceptance:**
- Custom session/break lengths are persisted to backend
- Settings survive app restart
- Settings are applied to all new sessions created after the change

**Risk:**

None identified.
