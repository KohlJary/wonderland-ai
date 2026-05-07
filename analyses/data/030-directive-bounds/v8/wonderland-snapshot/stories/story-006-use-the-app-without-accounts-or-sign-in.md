## Story 006: Use the app without accounts or sign-in

**Persona:** All of the above personas, who have app-fatigue and do not want to deal with auth. Also: Marcus, who is skeptical of SaaS and will not use an app that requires an account.

**Situation:**

The user downloads the app. They want to use it immediately — no account creation, no email verification, no password. Just start a session.

**Need:**

As anyone, I want to open the app and immediately use it without creating an account or signing in, so that I can try it and decide whether it works for me before committing any identity to it.

**Acceptance:**
- First launch: the app shows the session start button, not a sign-in screen.
- All data is stored on the device locally; no backend account is required.
- If I uninstall and reinstall the app, the history is gone (because it was local). The app tells me this is how it works.

**Tier:** core

**Confusion-flags:**
- The directive says 'design with a real database so multi-user can be added later.' This creates a design question: should the local data be synced to a backend (optionally), or should the backend be separate? If synced, then uninstalling loses history only if the user never signed up. If separate, then auth is a second feature. I'm not going to specify — this is a Cat/Tweedle decision. But it is a real fork in the architecture.
