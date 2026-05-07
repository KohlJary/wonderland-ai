## Test Scenario 008: Alex customizes his focus rhythm (User Journey)

**Feature:** Customize session and break durations (feature-004)
**Persona:** Alex, 35, manager. Takes many 1-on-1 calls and context-switches frequently. The standard 25/5 pomodoro is too long; he needs 15-minute sessions and 2-minute breaks.
**Stack span:** frontend + backend
**Severity:** high
**Concern:** User happiness — does Alex find the settings intuitive, and do his custom durations actually apply to his next session?

**User Journey:**

Alex opens the app. He's used it with the default 25/5 rhythm for a week, but he realizes the default doesn't fit his workday. He taps on "Settings" (or a gear icon on the main screen).

The settings screen shows two fields:
- Session duration: 25 minutes
- Break duration: 5 minutes

Next to each field is a description: "Session duration applies to the next session you start. Completed sessions are not affected."

Alex taps the "Session duration" field. A number input (or slider, or +/- buttons) appears. He changes it from 25 to 15. He taps the "Break duration" field and changes it from 5 to 2.

Below the fields, he sees a summary: "Next session: 15 min, Next break: 2 min" to confirm his changes.

He taps "Save" or the change auto-saves (with a "Saved" confirmation). The settings screen closes.

Alex goes back to the main screen. He sees the updated default timer display: "15:00" instead of "25:00". He's satisfied.

He taps "Start Session." The timer counts down from 15 minutes. When it completes, the break timer appears: "2:00" and counts down. After the break, a new session starts with 15 minutes again.

Two weeks later, Alex is having a lighter day with fewer calls. He wants to try a deeper focus rhythm. He goes back to settings and changes the session duration to 45 minutes and the break duration to 10 minutes. He confirms the change.

The next session he starts uses the new 45/10 rhythm. His previously completed sessions still show their original durations in the history (the 15-minute sessions from two weeks ago are not retroactively changed).

**Observable User States the Frontend Must Handle:**

- `settings_closed` — Main screen, settings gear icon visible
- `settings_open` — Settings screen with duration fields displayed
- `settings_editing` — User is interacting with the duration input (spinner, slider, keyboard input)
- `settings_validating` — Checking if the new values are within allowed bounds (e.g., 1–120 minutes)
- `settings_saving` — Submitting the new settings to the backend (brief state)
- `settings_saved` — Confirmation: "Settings saved" or similar
- `settings_error` — Backend rejected the new settings (e.g., out-of-bounds value); show error and allow retry
- `settings_offline` — No network; queue the settings change locally and sync when reconnected

**Frontend Responsibilities:**

1. On "Settings" tap, fetch GET /settings to display the current values
2. Provide input fields (number input, slider, or +/- buttons) for session and break durations
3. Validate on the frontend: session duration must be 60–7200 seconds (1–120 minutes); break duration must be 60–600 seconds (1–10 minutes)
4. Show validation errors immediately if the user enters an out-of-bounds value
5. On "Save", send a PUT /settings request with the new values
6. If the request succeeds, confirm the save and close the settings screen
7. If the request fails (400, 500), show an error and allow retry
8. Store the new settings in client-side state so the main screen timer immediately shows the new default
9. If offline, queue the settings change; on reconnect, retry the PUT request
10. Show a summary line (e.g., "Next session: 15 min") to help the user confirm their choice before saving

**Frontend-Backend Contract Points Exercised:**

- GET /settings returns current session_duration_seconds and break_duration_seconds
- PUT /settings accepts both fields or just one (partial update)
- Durations must be in seconds (not minutes) on the wire
- PUT /settings returns a settings_updated_at timestamp (for versioning)
- New settings apply only to the *next* session started; completed sessions are not affected
- Settings changes are atomic (both fields update together, or neither if validation fails)

**Failure Modes the Frontend Must Gracefully Handle:**

- User enters "0" for session duration → validate on frontend and reject before sending to backend
- User enters "999999" for session duration → validate on frontend and reject (max is 7200 seconds = 2 hours)
- Backend returns 400 Bad Request on PUT /settings → show the error message and allow retry
- Backend returns 409 Conflict (race condition with concurrent settings update) → show "Settings were updated by another device; refreshing..." and fetch fresh settings
- Network drops mid-PUT → queue the request; on reconnect, retry (idempotent due to version timestamp)
- User changes settings mid-session → don't apply the change to the running session; apply to the next one
- User changes settings, then immediately starts a new session → the new session uses the freshly-saved settings
- Two devices update settings simultaneously → backend resolves via settings_updated_at timestamp; frontend shows the winning version

**Expected Outcome:**

Alex customizes his rhythm in under 30 seconds. The changes are immediately visible in the UI (the timer default updates). The next session he starts uses the new durations. His history is unaffected; old sessions show their original durations. He feels in control of his focus rhythm, not forced into a standard pattern.

**When This Test Passes:**

The frontend successfully:
- Fetches and displays current settings
- Validates duration inputs (min/max bounds) on the frontend
- Submits settings changes to the backend
- Updates the local timer defaults immediately on success
- Handles backend errors and validation failures gracefully
- Supports offline queueing and retry
- Ensures new settings apply only to future sessions, not completed ones
- Handles concurrent settings updates from multiple devices
