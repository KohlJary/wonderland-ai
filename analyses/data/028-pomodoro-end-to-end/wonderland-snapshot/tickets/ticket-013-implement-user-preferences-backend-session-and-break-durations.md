## Ticket 013: Implement user preferences backend—session and break durations

**Sources:** customize-session-and-break-lengths
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.75–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

Build a backend endpoint to store and retrieve user preferences: preferred session duration and preferred break duration. When the user customizes durations in the frontend, persist the preference. When the user starts a new session or break, use the stored preference as the default duration.

**Acceptance:**
- Preferences are stored in the database
- Endpoint returns the user's current session and break duration preferences
- Preferences persist across app restarts
- Defaults are sensible if the user has not customized (e.g., 25 min / 5 min)

**Risk:**

Clarify whether preferences are global or could be per-session in the future (future-proofing the schema now is easier than migrating later).
