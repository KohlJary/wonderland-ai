## Story 012: Maya loads her session after a day away—with explicit startTime semantics

**Persona:** Maya, 31, polyglot moderator. She closes the translation app after a session, comes back a day later, and expects her session state (active language pairs, last position in threads) to be exactly where she left it. She doesn't think about 'when the session started' — she thinks about 'my work, preserved.'

**Situation:**

Maya opened a session for English↔Spanish moderation. She added German↔French mid-session. She closed the app. 24 hours later, she reopens it on the same device. The server has her session record with startTime (when she first opened it) distinct from createdAt (when the record was created). When the app queries the session, startTime and createdAt are both present. Maya doesn't see either field—she sees her language pairs and her position, exactly as she left them.

**Need:**

As Maya, I want my session state (language pairs, thread positions, settings) to persist exactly across app close/reopen, regardless of how much time has passed, so that I can resume mid-sentence without re-initializing.

**Acceptance:**
- Query session after 24h: language pairs are identical to what was saved
- Query session after 24h: thread positions (last message read, scroll position) are identical
- Query session after 24h: settings (font size, notification prefs) are identical
- Response shape includes both startTime and createdAt; frontend reads startTime to measure session age if needed
- No defaults applied to missing date params in the query; explicit error if session_id is missing

**Tier:** core

**Confusion-flags:**
- startTime vs createdAt: the contract says they are distinct, but the user experience is 'my session is preserved.' I need to trust the backend semantics don't leak into the UI.
- UUID format: the contract locks UUID strings, not integers. I've written this story assuming that constraint is honored. If implementation diverges, the test will fail—which is correct.
