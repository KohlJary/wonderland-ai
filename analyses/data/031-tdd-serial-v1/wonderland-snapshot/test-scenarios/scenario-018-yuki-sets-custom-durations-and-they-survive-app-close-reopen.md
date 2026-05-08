## Scenario 018: Yuki sets custom durations and they survive app close/reopen

**Severity:** breakage

**Setup:**

Yuki opens the app for the first time on a fresh device. Default focus_duration is 25*60*1000 ms, break_duration is 5*60*1000 ms.

**Trigger:**

Yuki navigates to Settings, changes focus duration to 23*60*1000 ms and break duration to 7*60*1000 ms. She saves the settings. Then closes and reopens the app.

**Expected:**

On app reopen, Settings screen shows focus_duration: 23*60*1000 ms and break_duration: 7*60*1000 ms. The values she entered are still there.

**Concern:**

If localStorage is not being written, or if the app doesn't read from localStorage on startup, settings will reset to defaults on reopen. This breaks the entire feature for Yuki.

**Property:**

For all user-set settings S, after app close/reopen, Settings screen displays S unchanged.

**Implies:**
- Implies frontend implementation must use browser localStorage (or equivalent persistent client-side storage).
- Implies settings load during app initialization, not lazily.
