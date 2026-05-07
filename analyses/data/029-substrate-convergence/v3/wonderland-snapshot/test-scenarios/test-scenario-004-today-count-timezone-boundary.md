# Test Scenario 004: Today's session count respects user's local timezone, not UTC

**Severity:** silent-wrongness

**Setup:**

Jordan is using the app in the UTC-8 timezone (Pacific Time). It is 2025-01-15 at 10:00 PM Pacific Time (2025-01-16 at 06:00 UTC). Jordan has completed 4 focus sessions earlier today (Jan 15 PT). The app is open and showing the main screen with the session count.

**Trigger:**

The app loads /api/session-counts/today to fetch today's session count.

**Expected:**

The app displays "4 sessions completed today" (or similar). The count reflects sessions completed on 2025-01-15 Pacific Time, regardless of what UTC time it is.

**Concern:**

If the backend calculates "today" using UTC midnight:
- At 10 PM PT (6 AM UTC next day), the backend thinks it's tomorrow and returns an empty count (0 sessions).
- Jordan is confused: "I just completed a session but it's not showing in today's count."
- The count is wrong for the last 8 hours of every day (timezone offset).
- Users in timezone UTC+12 experience the opposite: sessions count as yesterday's until it reaches 12 PM their time.

This is silent wrongness: the app doesn't error, it just shows the wrong number. Users might assume the tracking feature is broken.

**Property:**

For all times T within the user's local date [T_midnight_local, T_midnight_local+24h):
- GET /api/session-counts/today returns the count of sessions with completed_at within that interval (user's local timezone).
- If the backend needs to infer timezone, it should either:
  - Accept a timezone parameter from the client.
  - Infer from the request (IP geolocation, Accept-Language, etc.) — less reliable but acceptable for v1.
  - Use a per-user stored timezone if multi-user support exists.
- For v1 single-user: use client's reported timezone offset or store it in Settings.

**Implies:**

- Implies timezone handling in the backend: either accepting a timezone parameter or inferring it — flag for Tweedledum.
- Implies frontend sending timezone to the backend (or frontend-only calculation of today's date) — flag for Tweedledee.
- Implies contract clarification on how "today" is defined (local vs. UTC) — likely already in contract-note-004.
