## Ticket 001: Initialize focus session with user-set duration

**Sources:** start-and-complete-a-focus-session
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1-2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: persist-focus-session-to-indexeddb, render-focus-session-completion-screen
- Blocked by: —
- Soft: —

**Description:**

User can initiate a focus session from the home screen by selecting a duration (default: 25 min). Session state is persisted to local storage. Timer begins immediately on confirmation. UI shows countdown in human-readable format (MM:SS). No server calls required in M1.

**Acceptance:**
- User can select a duration from a dropdown or input field (25, 45, 90 min presets + custom)
- Timer displays MM:SS format and counts down to 00:00
- Session data (start time, target duration, persona context) is written to local storage on initiation
- Focus session screen is non-dismissible while timer is running (user cannot accidentally close tab or navigate away without explicit end-session action)

**Risk:**

If custom durations are allowed, validation and edge cases (0 min, 99999 min) could expand scope. Recommend MVP: presets only.
