## Story 003: Deaf user reads live-captioned cross-language conversation

**Persona:** Sophie, 29, deaf, uses German Sign Language natively. She reads written German fluently. She was invited to a text chat that has English speakers. She wants to participate with the same access as hearing participants.

**Situation:**

Sophie sees the chat app. English messages appear. She can use a screen reader, but the real barrier is that she doesn't read English—she reads German. The app's translation feature could serve her need, but only if the translation is accurate enough to be her reliable access point, and only if she can be confident it's working.

**Need:**

As Sophie, I want English messages in the chat translated to German consistently and accurately, so that I have the same reading experience as German speakers and can participate fully without worrying that a mistranslation is creating a barrier I can't see.

**Acceptance:**
- English → German translations are available for every English message
- Translations appear within the same latency as for hearing German speakers (2-3 seconds)
- Sophie can see both original and translation (so she can catch a mistranslation if it happens)
- There is no additional accessibility barrier in the UI (contrast, font size, clickability all meet WCAG AA minimum)

**Tier:** core

**Confusion-flags:**
- This story assumes the translation quality is good enough to be Sophie's only access point. But what if translation is 90% accurate? At what point does mistranslation become a barrier equivalent to or worse than monolingualism? I don't know, and the team needs to think about this before launch.
- I assumed Sophie would want the same 2-3 second latency. But for a deaf person relying on translation for access, maybe seeing the original message come through first and waiting for translation is more reassuring (proof the message arrived) than having them sync. Or maybe it's more stressful. I'm guessing.
- GDPR applies (EU scope). Sophie's translation request log is potentially sensitive data. I don't know what the Queen's ruling on this will be, but I'm flagging that it matters.
