## Story 001: Monolingual book club member joins a cross-language discussion

**Persona:** Maria, 58, retired Spanish teacher, fluent in German but no English. She joined an online book club that has members from Berlin and London. She wants to participate in real-time discussion without translating every message herself.

**Situation:**

Maria is in a video call with the book club. The English speakers are typing messages in the chat. German speakers are responding in German. Maria reads German fine but feels excluded from English messages; she cannot contribute to conversations happening in English without stopping to use a separate translator, which breaks the flow.

**Need:**

As Maria, I want messages from English speakers to appear in German so I can read and respond in real time without context-switching, so that I feel like a full participant rather than someone who needs special accommodation.

**Acceptance:**
- When an English speaker sends a message in the shared chat, Maria sees it translated to German within 2-3 seconds
- When Maria sends a message in German, English speakers see it translated to English within 2-3 seconds
- Maria can see both the original message and the translation (original language in lighter text, her language prominent)
- No additional UI click or mode-switch required; translation happens by default

**Tier:** core

**Confusion-flags:**
- I wrote 'real time' but I'm not sure what latency Maria would actually tolerate—2-3 seconds feels right for async chat, but is it? This is worth testing with actual users.
- I assumed Maria wants to see the original too, but maybe seeing only German makes her feel fully included? Or does original-language visibility reassure her that translation is happening? I don't know.
- The 'lighter text' detail is a UX assumption I made; I don't actually know how to render this accessibly or if it's the right visual choice. That's the Tweedles' call.
