## Story 006: Trust that data persists across app restarts

**Persona:** Aaliyah, 29, a consultant who runs the app on her phone while traveling. She doesn't think about whether data persists — she just expects it to. If she closes the app and reopens it, today's session count should be there.

**Situation:**

Aaliyah finishes a focus session, closes the app to take a call, and reopens it an hour later. She expects her session history to be exactly as she left it.

**Need:**

As Aaliyah, I want my session history and settings to be saved locally so that they survive app closes, crashes, and phone restarts, so that I don't lose my progress or have to reconfigure.

**Acceptance:**
- Closing and reopening the app shows the same session history
- Session history persists through phone restarts
- Settings (custom session/break lengths) persist through app closes and restarts
- No manual 'save' required — everything is automatic

**Tier:** core

**Confusion-flags:**
- What happens if the user's phone runs out of storage? Should the app gracefully degrade, or fail loudly?
- Should old history be pruned after a certain point (e.g., delete sessions older than 1 year), or kept forever?
