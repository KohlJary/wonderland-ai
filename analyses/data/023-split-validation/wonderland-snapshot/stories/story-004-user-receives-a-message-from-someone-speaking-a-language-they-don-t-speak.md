## Story 004: User receives a message from someone speaking a language they don't speak

**Persona:** Yuki, 26, Japanese native speaker, works in tech in Osaka. She joined the book club to practice English reading. She does not speak German.

**Situation:**

A German member of the book club sends a message in German. Yuki's app receives it. She has selected Japanese as her reading language.

**Need:**

As Yuki, I want to read the German message translated to Japanese, so that I can understand what is being said even though I do not speak German.

**Acceptance:**
- The German message appears in Yuki's chat in Japanese translation
- Yuki can identify who sent the message and can reply to them (either in Japanese or English, depending on her choice)
- The translation is accurate enough for book club discussion (not perfect, but understandable)

**Tier:** core

**Confusion-flags:**
- At MVP launch, do we support English ↔ German and English ↔ Japanese, but NOT German ↔ Japanese? If Yuki receives German, does she get it via German → English → Japanese (lossy) or via a direct German → Japanese path?
- If there is no direct German → Japanese translation, how does the system communicate that to Yuki? Does the message say 'translated from German via English' or does she not see that?
- This is a real edge case for the MVP scope; should it be core or fast-follow?
