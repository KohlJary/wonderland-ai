## Story 006: Maya loads her session after a day away

**Persona:** Maya, 31, polyglot moderator. Manages cross-language book club threads. Last logged in yesterday; returning to check overnight activity.

**Situation:**

Maya opens the app after 18 hours away. She expects her prior context (which books she was moderating, which language pairs were active) to be exactly as she left it. She's annoyed when apps make her re-establish her state.

**Need:**

As Maya, I want the app to restore my exact prior session state (active threads, language pairs, scroll position in each) so that I don't lose continuity or have to re-navigate to where I was.

**Acceptance:**
- Session loads with same threads visible as when Maya last used the app
- Language pair selections are preserved
- No data is lost or reset between sessions
- Load completes within 2 seconds

**Tier:** core

**Confusion-flags:**
- Unclear whether scroll position / viewport state is part of 'session' or a fast-follow. Made assumption it's included but may need clarification.
- Not sure about conflict resolution if server has newer data than cached session — do we merge, or trust local cache as source of truth?
