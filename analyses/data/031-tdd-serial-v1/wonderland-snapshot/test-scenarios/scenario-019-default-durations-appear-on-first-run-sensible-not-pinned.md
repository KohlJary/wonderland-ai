## Scenario 019: Default durations appear on first run; sensible not pinned

**Severity:** degradation

**Setup:**

User opens the app for the first time. Settings have never been saved. App queries localStorage for settings.

**Trigger:**

User navigates to Settings screen. App loads defaults.

**Expected:**

Settings screen shows: focus_duration: 25*60*1000 ms (25 min), break_duration: 5*60*1000 ms (5 min), audio_enabled: true, audio_volume: 50, theme: 'light'. User can change any of these; they are not locked.

**Concern:**

If defaults are hardcoded in the UI layer and never written to localStorage, the second time the user opens Settings, the app might not persist their changes (because localStorage is still empty and the app just renders hardcoded defaults). Or defaults might be so restrictive that Yuki can't override them.

**Property:**

For all settings K with default D, if no value for K exists in persistent storage, the app displays D. Once user sets a value, that value overwrites D.
