## Story 002: Polyglot moderator manages cross-language thread without drowning

**Persona:** Marcus, 34, fluent in English, German, and Japanese, based in Berlin. He's moderating the book club and needs to track when translation is breaking down or when cultural context is getting lost in translation.

**Situation:**

Marcus speaks all three languages natively. When he sees Sarah ask a clarifying question, he realizes the translation of a German joke didn't carry the humor. When a Japanese member misunderstands a British idiom, Marcus has to step in. He's doing unpaid labor as a bridge, and he's exhausted.

**Need:**

As Marcus, I want to see which messages are original and which are translated, so that I can quickly spot where the translation is failing and jump in with cultural context before misunderstanding hardens.

**Acceptance:**
- Messages show a clear visual or textual indicator (label, icon, color) of 'original in this language' vs 'translated into this language'
- Marcus can see the original-language message and the translation side-by-side without clicking or expanding
- The UI doesn't require Marcus to be the app owner or admin — any member can see translation status

**Tier:** core

**Confusion-flags:**
- I'm assuming Marcus needs to see both languages at once, but maybe that's too noisy for a fast-moving chat. Maybe he only needs to tap/hover to see the original. This is a UX call I don't want to make without watching real usage.
- I don't know if translation quality metrics (confidence score, fallback-to-dictionary, etc.) should be visible to users. If the translation system says 'I'm 60% confident,' does that help Marcus or just create paranoia? This feels like something the Dormouse will tell us after we have real data.
