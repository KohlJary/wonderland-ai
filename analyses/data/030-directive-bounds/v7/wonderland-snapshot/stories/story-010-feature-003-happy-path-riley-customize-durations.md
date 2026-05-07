## Story 010: Feature 003 Happy Path — Riley customizes session and break durations

**Feature:** Customize session and break durations (feature-003)

**Persona:** Riley, 29, a developer who prefers 50-minute focus blocks and custom break lengths.

**Happy-path scenario:**

1. Riley opens the app. On the home screen, a "Settings" gear icon is visible in the top-right corner. Below the "Start Session" button, current settings are displayed: "50 min focus / 10 min break."

2. Riley taps Settings. A new screen opens with two sliders:
   - "Focus Duration: 50 min" (range: 5–60 min)
   - "Break Duration: 10 min" (range: 1–30 min)

3. Riley adjusts the focus slider to 60 min, the break slider to 15 min. Both sliders respond in real-time and display the new values.

4. Riley taps "Save" or the changes auto-save. A confirmation toast appears briefly: "Settings saved."

5. Riley returns to the home screen. The settings display now shows "60 min focus / 15 min break."

6. Riley starts a session. The timer counts down from "60:00." After the session ends and Riley starts a break, the break timer counts down from "15:00."

7. Riley adjusts settings again, changing break to 5 min.

8. The in-progress break is *not* retroactively adjusted — it continues counting down from 15 min (not 5 min). Only the next session and break will use the new 5-min default.

9. Riley closes the app and reopens it hours later. The home screen still displays "60 min focus / 5 min break" — settings persisted.

10. Riley starts a new session, and the timer counts down from 60 min as expected.

**Expected result:**

Riley can customize timers without friction. Settings persist across sessions and app restarts. Changes apply prospectively (next session), not retroactively (current session).

**Contract assumptions validated:**

- Settings are fetched from GET /settings on startup.
- Settings are patched via PATCH /settings on user change.
- Settings are cached locally (survived app restart without network).
- Settings apply to the next session, not the in-progress one.
