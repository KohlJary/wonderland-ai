## Story 007: Kenji adds a new language pair mid-session

**Persona:** Kenji, 26, translator. Uses the app to manage live translation requests in real time. Frequently adds new language pair support as new clients arrive.

**Situation:**

Kenji is mid-session, actively moderating Japanese→English threads. A new client arrives needing Chinese→English support. He clicks 'add language' and selects Chinese.

**Need:**

As Kenji, I want to add a new language pair without losing any active threads or requiring a session reload, so that I can respond to new client needs without interruption.

**Acceptance:**
- New language pair appears in the active list immediately
- Existing threads remain active and unaffected
- Settings persist after adding the new pair
- No session interrupt or reload occurs

**Tier:** core

**Confusion-flags:**
- Unclear if 'add language pair' triggers a settings save, or if it's buffered until explicit save. Contract notes mention 'settings operations' but not the exact trigger timing.
- Not sure whether adding a pair should broadcast to server immediately or wait for session sync.
