## Contract Note 006: Settings persistence and live application

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No contract yet; establishing baseline

**Proposed Change:**

Settings (session_duration_minutes, break_duration_minutes, optionally: auto-start-break, notification-enabled) live in database, fetched on app startup and cached in React state. Settings changes persist immediately (POST /api/settings or PATCH /api/settings/{key}). When settings change, frontend applies new durations to the *next* session, not the running one. Running session ignores setting changes.

**Source:** feature-004 (customize session and break durations)

**Frontend Impact (Tweedledee):**

pending

**Backend Impact (Tweedledum):**

Your POST/PATCH pattern maps to single settings record per user with last-write-wins semantics. I can do that, but I want to surface a boundary question: do settings changes take effect on the running session, or only on the next session? Your note says 'next session only,' which is the right call — it means no mid-session state change, the invariant is clean. But that's a frontend responsibility (frontend must cache settings on session start, ignore subsequent changes until next session start). Backend just needs to enforce bounds: session_duration_seconds in [60, 7200], break_duration_seconds in [60, 7200]. GET /settings returns current; PUT /settings (body with either or both fields) validates and writes, returns updated record. No versioning, no conflict resolution.
