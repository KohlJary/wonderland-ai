## Story 004: Persistent Settings

**Persona:** Yuki, 26, grad student, tried three different Pomodoro apps before finding one. She has her timing dialed in (23 minutes focus, 7 minutes break — not standard, but it works for her concentration rhythm). She needs settings to stick so she doesn't reconfigure every session.

**Situation:**

Yuki opens the app multiple times per day across different devices and contexts. If her settings reset to defaults each time, the app becomes friction instead of help.

**Need:**

As Yuki, I want my focus/break durations to persist across app sessions so I don't have to reconfigure my rhythm every time I open the app.

**Acceptance:**
- Focus session duration setting persists (survives app close/reopen)
- Break duration setting persists
- If user accesses app on a new device, reasonable defaults appear (user can save custom settings)
- Settings are editable without breaking the current or upcoming timer

**Tier:** core

**Confusion-flags:**
- Unclear: if Yuki uses the app on phone and laptop, are settings synced across devices, or stored separately per device? (affects sense of 'persistent')
  - **RESOLVED (ADR-001):** settings are local-first, stored per-device only. v1 does not sync across devices.
- Unclear: where does she access settings — in-app menu, separate settings screen, or part of the daily review?
  - **RESOLVED (Feature contract):** settings have a dedicated UI screen accessible from main timer view. Not embedded in daily review.

**User Journeys:**

**Journey 1: Yuki sets custom durations and they persist**
- Yuki opens the app for the first time and sees defaults (25 min focus, 5 min break)
- She navigates to Settings
- She changes focus duration to 23 minutes, break duration to 7 minutes
- She saves settings
- She closes the app
- She reopens the app
- Settings still show 23/7 — her custom rhythm is preserved
- She starts a focus session and it runs for 23 minutes (not 25)

**Journey 2: Yuki accesses the app on a new device**
- Yuki opens the app on a different device for the first time
- Settings show defaults (25 min focus, 5 min break)
- She configures her rhythm (23/7) as she did on the first device
- Settings persist on this device independently (first device and second device are unsynced)
