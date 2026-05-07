## Test Scenario: Sam Adjusts Session and Break Lengths

**Severity:** degradation (if this fails, users are locked into 25/5 pomodoros)

**Setup:**

Sam is a 42-year-old writer who tried traditional 25/5 pomodoros but found they didn't match her natural rhythm. She prefers 50-minute sessions and 10-minute breaks. She opens the settings screen.

**Trigger:**

Sam taps on Settings. She sees two fields: "Session Length (minutes)" set to 25, and "Break Length (minutes)" set to 5. She changes them to 50 and 10, respectively, and taps Save.

**Expected:**

1. GET /config returns current configuration with session_length_minutes=25, break_length_minutes=5
2. PATCH /config with JSON {session_length_minutes: 50, break_length_minutes: 10} returns HTTP 200
3. Response includes the updated config: session_length_minutes=50, break_length_minutes=10
4. Subsequent GET /config returns the new values
5. The next session Sam starts has target_duration_seconds = 50 * 60 = 3000
6. Config persists across app restarts (new client session would fetch the saved value)
7. Changes take effect immediately on the next session (no app restart required)

**Concern:**

The concern is that:
- Config values might not validate (zero, negative, or absurdly large values)
- PATCH might silently ignore the update (no error, but value doesn't change)
- Updated config might not be used on the next session (old default persists)
- Changes might require an app restart to take effect
- Fractional minutes (e.g., 25.5) might not be handled cleanly
- Changing one field might reset the other to default

**Property:**

For all users U and config C:
- PATCH /config with C' returns HTTP 200 and persists C'
- Subsequent GET /config returns C'
- For all sessions S started by U after PATCH, S.target_duration = C'.session_length_minutes * 60
- Config values must be positive and within reasonable bounds (e.g., 1–480 minutes)

**Implies:**

- Implies GET /config endpoint
- Implies PATCH /config endpoint with session_length_minutes and break_length_minutes fields
- Implies Config model and persistence layer (database table or settings store)
- Implies config is fetched and used at session-start time (not cached globally)
