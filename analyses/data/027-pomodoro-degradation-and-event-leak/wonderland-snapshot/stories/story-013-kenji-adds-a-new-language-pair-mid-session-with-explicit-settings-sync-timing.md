## Story 013: Kenji adds a new language pair mid-session—with explicit settings sync timing

**Persona:** Kenji, 28, language-exchange enthusiast. He's in the middle of a moderation session (English↔Japanese). He realizes he also needs to moderate Spanish threads. He adds Spanish↔Japanese to his session *right now*—not after closing and reopening.

**Situation:**

Kenji is actively moderating. He taps 'add language pair.' The app POSTs the updated session with the new pair. The server returns a 200 OK with the updated session state. Kenji immediately sees Spanish↔Japanese in his active pairs. If he closes the app and reopens it (on the same or a different device), the new pair is there.

**Need:**

As Kenji, I want to add a new language pair mid-session and have it take effect immediately in this session and persist to all my devices, so that I can adapt to urgent moderation needs without interruption.

**Acceptance:**
- POST new language pair: server returns 200 OK with updated session state
- New pair appears immediately in the frontend UI after the response
- Close and reopen the app on the same device: new pair is present
- Open the app on a different device: new pair is present (settings sync)
- No silent merges or conflicts when the same session is opened on two devices; contract guarantees last-write-wins with no user-visible conflict

**Tier:** core

**Confusion-flags:**
- Settings sync timing: the contract says the POST response is authoritative, but does sync to other devices happen *immediately* or after a grace period? The story assumes immediate—but if there's eventual consistency, Kenji needs to see a notification, not silent divergence.
- Multi-device conflicts: the contract specifies last-write-wins, but I'm assuming the user never *sees* a conflict UI. If the team decides Kenji should see 'your other device is editing this session,' I need a new story for that user experience.
