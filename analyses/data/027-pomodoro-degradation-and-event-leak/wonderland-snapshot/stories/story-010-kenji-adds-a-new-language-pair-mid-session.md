## Story 010: Kenji adds a new language pair mid-session

**Persona:** Kenji, 26, software engineer who codes-switches between Japanese, English, and Mandarin. He's on video call with a collaborator and needs to switch language pairs without closing the session.

**Situation:**

Kenji is in the middle of a session viewing Japanese→English translation pairs. His collaborator asks a question in Mandarin. Kenji needs to add Japanese→Mandarin to his active pairs *right now*, mid-conversation.

**Need:**

As Kenji, I want to add a new language pair to my session while it's active, and see it immediately available for translation, so that I can respond to my collaborator without losing context or closing the app.

**Acceptance:**
- Add-language-pair UI appears without closing or reloading the session
- New pair is immediately available for lookup/translation
- The session's 'active pairs' list updates to include the new pair
- If Kenji is on multiple devices, the new pair is available on all devices within [DECISION NEEDED: immediately? on next sync? on app reopen?]

**Tier:** core

**Confusion-flags:**
- The acceptance criteria for 'available on all devices' depends on the contract decision about settings sync timing. If Kenji adds Japanese→Mandarin on his phone, does his desktop see it instantly, or only when he reopens the app? This changes the UX story for 'multi-device user'.
- Is 'add new pair' a UI action only (client-side), or does it require a server call? If server-side, what happens if the call fails mid-session—does the pair disappear from the local session?
- If this new pair addition gets overwritten by a concurrent edit from his desktop (last-write-wins), does Kenji see a silent failure or a notification?
