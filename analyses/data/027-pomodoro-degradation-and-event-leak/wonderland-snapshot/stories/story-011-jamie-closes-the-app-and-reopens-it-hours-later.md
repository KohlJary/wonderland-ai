## Story 011: Jamie closes the app and reopens it hours later

**Persona:** Jamie, 19, first-year university student. Monolingual English speaker using the app to help with a French-language essay due tomorrow. Juggling homework, social media, and sleep deprivation.

**Situation:**

Jamie has been using the app to translate French passages for their essay. They close the app to do other homework. Hours later (app was killed by OS, device sleep, app backgrounding), they reopen it to continue translating.

**Need:**

As Jamie, I want my session—my translation history, my open documents, my search queries, my notes—to be available exactly as I left it, so that I can resume my homework without losing progress or context.

**Acceptance:**
- Session resumes with the same documents/passages loaded
- Search history and recent queries are available
- Any notes or marked translations persist
- Load time is under 3 seconds

**Tier:** core

**Confusion-flags:**
- Is 'session state' local-only (device storage), or synced to the server? If server-synced and Jamie gets a new device, should the session transfer? If local-only, does session data survive an app uninstall/reinstall?
- What constitutes 'session'—just the current translation task, or the full app state (settings, language pairs, history)? My acceptance criteria assume both; that might be overreach.
- If hours elapse and the server discards old sessions (cache eviction, data retention policy), what does Jamie see when they reopen—a partial state, a cleared slate, or an error?
