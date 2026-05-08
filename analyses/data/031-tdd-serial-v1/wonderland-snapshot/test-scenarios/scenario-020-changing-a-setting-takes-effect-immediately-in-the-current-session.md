## Scenario 020: Changing a setting takes effect immediately in the current session

**Severity:** degradation

**Setup:**

User is in the middle of a work session (e.g., focus timer is running, or about to start a break). User opens Settings and changes break_duration from 5 to 10 minutes.

**Trigger:**

User saves the setting change and returns to the main timer view. A break session is about to start.

**Expected:**

The new break_duration (10 min) is used for the break that is about to begin. User does not have to restart the app for the new duration to take effect.

**Concern:**

If the app caches settings in memory and doesn't reload from localStorage after the user changes them, the old duration will still be used until app restart. This is jarring and breaks the 'takes effect immediately' promise.

**Property:**

For all settings changes made in the current session, subsequent session-start calls use the new values without app restart.

**Implies:**
- Implies settings changes must invalidate any in-memory cache (or there is no cache, and every session-start reads from persistent storage).
