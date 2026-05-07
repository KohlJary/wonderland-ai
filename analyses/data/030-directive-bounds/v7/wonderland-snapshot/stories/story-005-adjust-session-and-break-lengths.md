## Story 005: Adjust session and break lengths

**Persona:** Riley, 29, a developer who uses 50-minute focus blocks instead of 25, and wants breaks they can configure per their energy.

**Situation:**

Riley opens the app and sees default timers (25 min focus / 5 min break). They know themselves; 25 is too short. They need to customize without breaking their workflow.

**Need:**

As Riley, I want to adjust the focus session length and break length to match my rhythm, so that the app works *for* me instead of against me.

**Acceptance:**
- Riley can access a settings screen from the home screen
- Settings let Riley set custom focus duration (in minutes) and break duration (in minutes)
- Changes apply to the next session they start
- Riley can see their current settings (so they know what they chose) without re-entering settings every time

**Tier:** core

**Confusion-flags:**
- Can Riley change settings mid-session? If they're 10 minutes into a 25-minute session and change the session length to 50, does it apply retroactively? I'm guessing not — it applies next session. But this is a UX detail I'm unsure of.
- What's the range of acceptable values? Can someone set a 5-hour session? A 30-second break? The app needs guardrails, but I don't know what they should be.
