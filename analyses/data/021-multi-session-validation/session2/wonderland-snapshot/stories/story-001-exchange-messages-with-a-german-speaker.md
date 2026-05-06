## Story 001: Exchange messages with a German speaker

**Persona:** Sam, 28, English-only book club organizer in London. Joined an EU-wide reading group and wants to chat with members in real time without switching to Google Translate. Reads German *slowly* in books; speaks almost none.

**Situation:**

Sam's reading group has a live chat during their weekly meeting. The group is split: English speakers and German speakers. Sam is coordinating the discussion but can't follow the German side. Right now someone copy-pastes messages into a translator; it's clunky and breaks the flow.

**Need:**

As Sam, I want to read and respond to German speakers in my reading group in real time with translation handled transparently, so that I can participate fully without the translator-switching friction.

**Acceptance:**
- Sam types a message in English and sends it.
- The message appears in the chat immediately in both English and German.
- A German speaker can read Sam's message in German without delay.
- A German speaker types in German; Sam receives the German text and sees it auto-translated to English below or alongside.
- The conversation flow feels natural — not 'message, pause, translate, resume'.
- Sam can see who sent each message and in what language it was originally written.

**Tier:** core

**Confusion-flags:**
- How does auth work for 'two users'? Are they pre-registered? Is there a login flow or a join link? The directive says 'basic auth' but I'm not sure what that means in context — HTTP basic, token, session cookie?
- GDPR applies. Where do the messages live? Are they stored? For how long? Who can access them? Do users get a data deletion mechanism? I feel like this is load-bearing but I'm not sure if it shapes the MVP or comes after.
- What happens if translation fails or is ambiguous? Does the user know? Do they get an error, or a best-guess, or a note that something was unclear?
