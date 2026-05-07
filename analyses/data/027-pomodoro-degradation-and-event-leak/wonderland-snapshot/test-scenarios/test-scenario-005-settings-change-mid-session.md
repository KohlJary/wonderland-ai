## Scenario: User adjusts focus duration to 5 minutes mid-session; existing session ignores the change

**Severity:** degradation

**Setup:**
User has a session in progress with targetDuration=25 minutes. The session has been running for 10 minutes (15 remaining). User navigates away from the timer view to the Settings view.

**Trigger:**
User adjusts the 'Focus Duration' setting from 25 minutes to 5 minutes. User confirms/saves the setting. The app persists the new duration. User navigates back to the timer view.

**Expected:**
The timer for the in-progress session still shows 15 minutes remaining (25 - 10 elapsed, not recalculated from the new 5-minute setting). The settings change affects only *new* sessions started after the change. The in-progress session completes with actualDuration=25 (its original targetDuration).

**Concern:**
I suspect the app applies the settings change globally (at render time), and the in-progress timer might flip to '5:00' suddenly, confusing the user. Or the team might not have distinguished between 'apply settings' (one-time, at session creation / POST time) vs. 'pull settings' (continuous, at render time / each frame). If settings are pulled at render time, and the user changes them, the timer resets to the new duration. Alternatively, the targetDuration in the session record might be replaced with the new setting value, corrupting the session's immutable contract.

**Property:**
For all in-progress sessions: the targetDuration is immutable and set at session creation time (POST /sessions). Settings are applied only at the moment of session creation. Changes to settings do NOT affect running sessions, only new sessions created after the change. A session's targetDuration never changes during its lifetime.

**Implies:**
- Implies session record immutability: targetDuration is part of the session record (persisted in the session model/table), not looked up from settings at render time. The session's actual value is authoritative, not re-derived from settings. Flag for Tweedledum and Tweedledee.
- Implies separation of concerns: settings (user preferences) and sessions (runtime instances) are separate. A session created with 25-minute duration carries that value forever. Flag for architecture review with Cat.
