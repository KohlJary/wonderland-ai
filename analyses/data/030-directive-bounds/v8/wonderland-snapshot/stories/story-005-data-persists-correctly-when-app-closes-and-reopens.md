## Story 005: Data persists correctly when app closes and reopens

**Persona:** Same as Devon — people who are tracking and reviewing history rely on it being trustworthy. If the app crashes mid-session, the session should either complete or be discarded, not left in an ambiguous state.

**Situation:**

The app is running a session. The phone crashes, or the user force-closes the app, or the OS kills it to free memory. The user opens the app again. They want to know: was that session counted or not?

**Need:**

As someone tracking my focus patterns, I want the app to handle crashes and force-closes gracefully, so that my history is accurate and I can trust the numbers.

**Acceptance:**
- If a session is interrupted (crash, force-close, OS kill), the session is either completed (if >50% of time elapsed) or discarded (if <50% elapsed). The user can see in history which happened.
- All completed sessions are written to the history immediately after completion, not batched until app close.
- If the user restarts the app mid-session, the session timer resumes where it left off (or can be reset, but the default is resume).

**Tier:** core

**Confusion-flags:**
- The '50% elapsed' threshold is arbitrary. The team will know better whether this is the right cutoff or whether there is a cleaner way to handle partial sessions. What matters is that the decision is made consciously, not left ambiguous.
- Recovery from crash — should the user be prompted 'you were in a session, resume or discard?' or should it be automatic? This is a UX decision the team will make, but worth noting that different users will have different preferences.
