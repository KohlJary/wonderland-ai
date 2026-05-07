## Story 005: Customize session and break lengths

**Persona:** Alex, 35, a manager who takes many 1-on-1 calls and context-switches frequently. The standard 25-minute session is too long; he needs 15-minute focus bursts, and 2-minute breaks to prepare for the next call.

**Situation:**

Alex opens the app settings. He realizes the default 25/5 pomodoro rhythm doesn't fit his workday. He wants to change it to 15/2 without having to build his own timer app.

**Need:**

As Alex, I want to change the session and break lengths in settings, so that the app adapts to my actual work rhythm instead of forcing me into a standard pattern.

**Acceptance:**
- Settings has fields for 'Session length' and 'Break length', defaulting to 25 and 5 minutes
- I can change both values to any length I want (e.g., 15-minute sessions, 2-minute breaks)
- The app remembers my settings and applies them to all new sessions
- Settings apply immediately; I don't need to restart the app

**Tier:** enrichment

**Confusion-flags:**
- Should there be guardrails (e.g., session must be at least 1 minute, at most 60)? Or should the app trust the user?
- Can the user have multiple 'profiles' (one for call-heavy days, one for deep-work days) or is a single setting sufficient for v1?
