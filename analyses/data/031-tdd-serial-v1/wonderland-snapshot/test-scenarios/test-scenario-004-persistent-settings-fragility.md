## Test Scenario 004: Persistent Settings — Fragility & Edge Cases

**Feature:** Feature 004 (Persistent Settings)
**Persona:** Yuki
**Stack:** frontend (all storage is client-side)
**Severity mix:** P0 (data loss) + P1 (graceful degradation)

---

### Scenario A: Storage is unavailable or full — graceful fallback to defaults

**Given:** app attempts to save settings but storage is inaccessible (quota exceeded, localStorage disabled, or permission denied)

**When:**
1. user changes settings and clicks Save
2. storage write fails (simulated: mock localStorage.setItem to throw)

**Then:**
- UI shows error message (e.g., "Could not save settings. Using defaults. Please try again later.")
- Form is not closed; user can retry Save
- Settings in memory revert to last successfully-saved state (or defaults if none saved before)
- App continues to function with defaults (settings screen is not blocked)
- If user closes settings without retrying, defaults are used for next timer

**Observable state transitions:**
- Save button is disabled until retry succeeds
- Error message is dismissible but persistent until cleared by successful save
- App does NOT crash; degrades gracefully

**Test contract:** mock `localStorage.setItem` to simulate quota exceeded or permission error

---

### Scenario B: Corrupted settings data in storage — fall back to defaults

**Given:** localStorage contains malformed settings (e.g., `focus_duration = -100`, `break_duration = 0`, `audio_volume = 200`)

**When:** app loads and reads settings from storage

**Then:**
- App detects invalid values (duration <= 0, volume outside 0-100)
- Invalid settings are rejected; app falls back to defaults
- Settings screen shows defaults (not corrupted values)
- Error is logged (developer visibility) but not shown to user (no panic)
- On next settings save, valid values are written (corrupted data is overwritten)

**Observable state transitions:**
- App loads and displays defaults (no visible corruption)
- If user subsequently opens Settings, they see clean defaults
- No broken UI or crashed timers

**Test contract:** write corrupted JSON to localStorage, verify app recovers

---

### Scenario C: Settings change while timer is running — new duration takes effect on next timer

**Given:** a 25-minute focus session is running (10 minutes elapsed, 15 minutes remaining)

**When:**
1. (while timer is running) user navigates to Settings
2. user changes focus_duration from 1500s to 1200s (20 minutes)
3. user saves and closes Settings
4. current timer continues and completes at 25 minutes (original duration)
5. (on next focus session) user starts a new focus session

**Then:**
- Current timer in progress is not affected — still runs for full original duration (25 min)
- Next focus session uses new duration (20 minutes)
- Break duration applies immediately if changed (if user is between focus/break boundary, new break duration is used)

**Observable state transitions:**
- Active timer display is NOT re-rendered when settings change
- Next timer creation reads current settings from storage

**Test contract:** during active session, call settings update; verify current timer duration is unchanged; start new session and verify new duration applies

---

### Scenario D: Theme change takes effect immediately without restart

**Given:** app is open with theme=light

**When:**
1. user navigates to Settings
2. user toggles theme to dark
3. user saves

**Then:**
- App UI immediately switches to dark theme (no page reload, no app restart)
- Settings screen remains open and is now rendered in dark theme
- All UI elements (timer display, buttons, backgrounds) switch theme

**Observable state transitions:**
- Theme update is synchronous (not deferred)
- No visual flash or blank screen during transition
- All UI components respond to theme change (no partial updates)

**Test contract:** theme state is observable in DOM; change theme setting and verify DOM reflects change immediately

---

### Scenario E: Audio volume setting persists even when audio is disabled

**Given:** settings show audio_enabled=true, audio_volume=50

**When:**
1. user disables audio (audio_enabled=false)
2. user later saves settings
3. time passes, user re-enables audio (audio_enabled=true)

**Then:**
- Volume is restored to 50 (not reset to default 50)
- If audio_enabled was changed to false without changing volume, volume is preserved in storage
- User can toggle audio on/off without losing preferred volume

**Observable state transitions:**
- Audio volume field is editable even when audio_enabled=false
- When audio_enabled toggles to true, volume reflects the saved value (not reinitialized)

**Test contract:** disable audio, change volume, save; later enable audio; verify volume is the previously-saved value
