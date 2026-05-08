## Ticket 003: Persist session settings and configuration across app launches

**Sources:** persistent-settings-across-app-launches
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: daily-review-of-session-history
- Blocked by: break-timer-with-user-configuration
- Soft: —

**Description:**

Implement persistent storage (localStorage or equivalent) to save user's preferred focus and break durations. Load settings on app startup and apply them as defaults. Do not persist session history yet.

**Acceptance:**
- User's focus and break durations are saved when set
- Settings are restored on app restart
- User sees their saved values when opening the app again
- Default values are sensible if user has never customized

**Risk:**

Storage mechanism choice (localStorage vs. indexedDB) depends on data scale and concurrency model — frontend and backend should align on schema early. May require contract negotiation between Tweedles.
