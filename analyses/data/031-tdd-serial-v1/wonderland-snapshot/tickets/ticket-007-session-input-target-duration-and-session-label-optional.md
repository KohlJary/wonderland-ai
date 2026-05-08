## Ticket 007: Session input: target duration and session label (optional)

**Sources:** focus-session-timer
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: focus-session-frontend
- Blocked by: —
- Soft: —

**Description:**

Before a focus session starts, the user picks a target duration (e.g., 25 min preset, or custom entry). Optionally, they can label the session (e.g., 'Design Review', 'Code Review', 'Writing'). Store the label with the session for later review. This is the 'setup screen' that precedes the timer.

**Acceptance:**
- User can select a preset duration (15 min, 25 min, 45 min) or enter custom
- User can optionally enter a session label
- Label is stored with the session and visible in daily review

**Risk:**

Low. This is a form capture layer.
