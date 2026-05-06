## Story 003: Second language pair works the same way (English ↔ Japanese)

**Persona:** Yuki, 28, Tokyo-based, native Japanese speaker. Works in tech, types primarily in Japanese, reads English but slower. Wants the same chat experience with an English speaker.

**Situation:**

Yuki is in a video call with an English colleague, Michael, and they want to chat in parallel about technical details. Yuki types in Japanese; Michael types in English. Both want the messages to land translated and readable in real-time.

**Need:**

As Yuki, I want to message Michael in Japanese and have him see it in English instantly, and see his English messages translated to Japanese, so that neither of us has to slow-think the language layer.

**Acceptance:**
- Yuki can start a conversation with Michael (English speaker)
- Yuki types a message in Japanese and sends it
- Michael receives it translated to English within 1-2 seconds
- Michael types in English; Yuki receives it translated to Japanese within 1-2 seconds
- Yuki and Michael each see the full history with both original and translation for every message

**Tier:** core

**Confusion-flags:**
- The directive specifies 'English ↔ German, English ↔ Japanese' — does this mean English is a hub, or are arbitrary pairs supported? If only hub-and-spoke, what happens if a German speaker tries to message a Japanese speaker? Probably out of scope, but worth naming.
- Japanese translation quality is notoriously harder than European languages. If the MVP launches with poor Japanese translations, does Yuki blame the product or accept it as v1? I'm assuming v1 will be imperfect; the acceptance criteria above don't specify quality. That might be a Queen/Dormouse decision, not mine.
- Character encoding and rendering — is this a known-solved problem in the stack, or a gotcha? I'm flagging it as something that could bite if not pre-checked.
