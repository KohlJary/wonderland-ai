## Ticket 002: Add configurable session durations (focus/break lengths)

**Sources:** break-timer-with-user-configuration
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: persistent-settings-across-app-launches
- Blocked by: focus-session-with-visual-countdown
- Soft: —

**Description:**

Add UI controls to let users configure focus duration (default 25 min) and break duration (default 5 min) before a session starts. Store user input in component state. Do not persist settings across app launches yet.

**Acceptance:**
- User can adjust focus duration before starting a session
- User can adjust break duration before starting a session
- Timer respects the configured durations
- Reasonable input bounds enforced (e.g., 1–120 min for focus, 1–30 min for break)

**Risk:**

Input validation edge cases (non-numeric input, zero, negative). Allocate 0.25 days if validation needs to be strict.
