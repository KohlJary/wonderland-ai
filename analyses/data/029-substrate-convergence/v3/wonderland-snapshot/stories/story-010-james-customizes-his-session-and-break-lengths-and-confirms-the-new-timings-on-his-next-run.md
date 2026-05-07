## Story 010: James customizes his session and break lengths and confirms the new timings on his next run

**Persona:** James, 42, freelance writer, prefers 50-minute work sessions and 10-minute breaks (not the default 25/5). He opens Settings once during onboarding and sets his preferences.

**Situation:**

James installs the timer, opens Settings, changes 'Session Length' from 25 to 50 and 'Break Length' from 5 to 10, saves, and closes Settings. Next, he starts a session to confirm the timer counts down from 50 minutes, not 25.

**Need:**

As James, I want to customize the default session and break lengths, so that the timer respects my preferred rhythm instead of forcing me to use the Pomodoro standard.

**Acceptance:**
- The Settings page displays two input fields: 'Session Length (minutes)' and 'Break Length (minutes)'.
- James can enter any positive integer (e.g., 50, 10) into these fields.
- When James saves Settings, the app stores his preferences (persists them across app restarts).
- The next time James starts a session, the timer counts down from his custom session length (50 min), not the default (25 min).

**Tier:** enrichment

**Confusion-flags:**
- What happens if James enters a negative number, zero, or a non-integer (e.g., 25.5)? Should the UI prevent invalid input, or should the backend validate and reject? The acceptance criterion doesn't address malformed input.
- Is there a 'Reset to Defaults' button in Settings, or does James have to manually re-enter 25/5 if he changes his mind? Probably should exist, but it's not in the acceptance criterion.
- Does changing Settings apply to sessions already in progress, or only to new sessions? The criterion says 'the next time' — so new sessions only. But the vagueness here could trip implementation.
- Are there any constraints on the max values (e.g., no sessions longer than 120 minutes)? Or can James set a 1000-minute session if he wants? The criterion doesn't bound this.
