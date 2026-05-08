## Story 004: Persistent settings across app launches

**Persona:** Sara, 26, student, lives in dorms and uses her phone for everything. She configures the timer once (25-min focus, 10-min break) at the start of the semester and never wants to touch settings again.

**Situation:**

Sara closes the app after a morning study session. She opens it again in the afternoon. She expects her break length to still be 10 minutes. She never wants to reconfigure.

**Need:**

As Sara, I want my timer settings and preferences to persist between sessions, so that the app stays out of my way once it's set up.

**Acceptance:**
- Session length setting persists across app close/reopen
- Break length setting persists across app close/reopen
- If I change a setting, it becomes the new default for all future sessions
- There's an easy way to reset to app defaults if I mess something up

**Tier:** core

**Confusion-flags:**
- Should the app remember what the user was in the middle of if they force-close mid-session? Probably not, but it's unclear.
- Is there a 'session length' setting separate from 'break length,' or are there more granular settings?
- Does 'persistent' mean local device storage, or cloud sync if the user reinstalls?
