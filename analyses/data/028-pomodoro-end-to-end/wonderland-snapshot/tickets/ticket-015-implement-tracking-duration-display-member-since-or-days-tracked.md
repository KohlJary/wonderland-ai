## Ticket 015: Implement tracking duration display—'member since' or days tracked

**Sources:** understand-how-long-the-app-has-been-tracking-sessions
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–0.75 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: app-launch-date-tracking
- Soft: —

**Description:**

Display the app launch or tracking start date on the main screen or in a profile view. Format could be 'Tracking for 47 days' or 'Member since Jan 15, 2025'. This is a simple calculation (today - launch_date) but gives the user a sense of their investment in the habit.

**Acceptance:**
- Tracking duration is displayed in a user-friendly format
- Duration is calculated correctly (today - launch_date)
- Display updates daily or on app launch

**Risk:**

Timezone edge cases for 'today'; use server time or user local time consistently.
