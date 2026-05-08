## Test Scenario 004: Persistent Settings — Happy Path

**Feature:** Feature 004 (Persistent Settings)
**Persona:** Yuki
**Stack:** full-stack (frontend storage + optional backend validation)
**Severity:** P0 (core acceptance criterion)

### Scenario A: Settings persist across app session boundaries

**Given:** app is open with default settings (focus_duration=1500s, break_duration=300s)

**When:**
1. user navigates to Settings screen
2. user changes focus_duration to 1380s (23 minutes)
3. user changes break_duration to 420s (7 minutes)
4. user clicks Save
5. app closes (or page navigates away and back)
6. app is reopened (fresh browser session, if web; app relaunched, if mobile)

**Then:**
- Settings screen shows focus_duration = 1380s, break_duration = 420s
- When user starts a focus session, timer runs for 1380 seconds (not 1500)
- When focus session completes and break auto-starts, break runs for 420 seconds (not 300)

**Observable state transitions:**
- Before save: settings form has unsaved changes indicator (or disabled Save button)
- After save: unsaved changes indicator gone, settings persisted to storage
- After reopen: settings restored from storage and displayed

---

### Scenario B: Audio and theme settings persist

**Given:** app is open with default settings (audio_enabled=true, audio_volume=50, theme=light)

**When:**
1. user navigates to Settings
2. user disables audio (audio_enabled=false)
3. user changes audio_volume to 75 (even though disabled — storage should preserve it)
4. user changes theme to dark
5. user saves
6. app closes and reopens

**Then:**
- Settings screen shows audio_enabled=false, audio_volume=75, theme=dark
- App UI uses dark theme immediately (no restart needed)
- If user re-enables audio, volume is restored to 75 (not reset)

**Observable state transitions:**
- Theme change reflects in real-time (no page reload required)
- Disabled audio setting suppresses alert sounds (tested in focus-session timer tests, not here)

---

### Scenario C: New device sees defaults, not synced settings

**Given:** Settings have been saved on device A (focus=1380s, break=420s)

**When:** user opens the app on device B for the first time (fresh storage)

**Then:**
- Device B shows default settings (focus=1500s, break=300s)
- User can save custom settings on device B
- Settings on device A are unchanged (no sync)

**Observable state transitions:**
- First app launch on new device triggers default-settings initialization
- Settings are isolated per-device (no shared backend state in v1)
