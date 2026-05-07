## Ticket 014: Implement app launch date tracking and display

**Sources:** understand-how-long-the-app-has-been-tracking-sessions
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: tracking-duration-display
- Blocked by: —
- Soft: —

**Description:**

Store the user's app launch date (or first session date) in the database. Expose this via an API endpoint so the frontend can display 'Tracking for X days' or 'Member since [date]'. This satisfies the persona's desire to understand how long they've been tracking sessions.

**Acceptance:**
- App launch date is recorded on first session or user signup
- Endpoint returns the launch date
- Date persists across sessions

**Risk:**

Deciding whether launch date is first session or account creation; clarify and document.
