## Story 005: Customize session and break lengths

**Persona:** Dev, 26, game developer who sometimes needs longer focus blocks. The standard 25/5 is great for email, but when deep in a coding feature, Dev wants to try 50-minute sessions with 10-minute breaks.

**Situation:**

Dev opens the Settings screen because the default durations don't match Dev's workflow. Dev needs to adjust both session length and break length, test them on a session or two, and save the preference.

**Need:**

As Dev, I want to change the session length and break length to match my work style, so that the timer fits my actual focus rhythm instead of forcing me into a pre-set mold.

**Acceptance:**
- The app has a Settings screen (accessible from the home screen or hamburger menu)
- Settings shows two editable fields: 'Session Length (minutes)' and 'Break Length (minutes)'
- Default values are 25 and 5, respectively
- The user can enter any positive integer (e.g., 50, 10)
- Changes are saved immediately and take effect on the next session start
- The app displays the user's current custom settings on the home screen (e.g., 'Session: 50 min | Break: 10 min') so they're always visible

**Tier:** core

**Confusion-flags:**
- Should there be bounds on the input (e.g., minimum 1 minute, maximum 120 minutes)? Or allow any duration? The directive doesn't constrain this.
- Should the user see a preview or confirmation before settings take effect, or is immediate application fine?
