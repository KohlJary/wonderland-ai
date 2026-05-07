## Story 006: View and understand local-first persistence

**Persona:** Alex, 29, a privacy-conscious developer, wants to know that his session data is stored locally and not uploaded anywhere.

**Situation:**

Alex is considering the app but hesitates because he doesn't want his work patterns tracked online. He wants confirmation that the data stays on his device.

**Need:**

As Alex, I want clear documentation that my session history is stored only on my device and not sent to any server, so that I can trust the app with my time-tracking data.

**Acceptance:**
- The app displays a clear statement (in settings, onboarding, or privacy section) that data is local-only
- No network requests are made except during optional export (if that feature exists)
- The app functions fully offline

**Tier:** enrichment

**Confusion-flags:**
- The directive says 'design with a real database so multi-user can be added later' — but it also says no auth, local app. I'm confused about whether a database already exists (backend, local SQLite, neither). This feels like an architectural decision that should happen before I finalize stories about persistence.
