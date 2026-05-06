## Story 005: User checks that translation happened correctly before relying on it

**Persona:** Henrik, 31, German engineer, reads English slowly. He is in a chat with English speakers and Japanese speakers. He wants to make sure a translation is accurate before responding, especially if the topic is technical.

**Situation:**

Henrik sees a message in Japanese. It's translated to German. The translation says something about 'API rate limits.' Henrik is not 100% sure if the original was about rate limits or quotas, and it matters for his response. He wants to see the original to verify.

**Need:**

As Henrik, I want to see the original-language message alongside the translation, so that I can spot-check for accuracy when the topic is technical or when I'm unsure.

**Acceptance:**
- Every translated message shows both original and translated text in the UI
- The original is visually distinguishable from the translation (e.g., smaller text, different color, or hover-over)
- Henrik can read the original without opening a modal or secondary panel—it's inline

**Tier:** core

**Confusion-flags:**
- I'm treating 'show original + translation side-by-side' as a core requirement, but earlier stories (James) might prefer *only* translation. Can both needs coexist in a single UI? Or do we need a toggle? I don't know if I'm scoping a conflict here.
- This assumes the app stores the original message. It probably does, but I'm flagging it as an assumption—if the app deletes originals after translation for privacy reasons, this story breaks.
- I don't know how much real estate showing original + translation takes up on a phone screen. This might force a design tradeoff the Tweedles will hit in implementation.
