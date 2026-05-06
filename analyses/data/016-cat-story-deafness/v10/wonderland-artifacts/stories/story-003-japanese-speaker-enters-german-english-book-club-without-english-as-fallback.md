## Story 003: Japanese speaker enters German-English book club without English as fallback

**Persona:** Yuki, 28, native Japanese speaker, studied German in university (B1 level), no English. She wants to join the book club but only two language pairs are launched at v1 (English ↔ German, English ↔ Japanese). She speaks German but not English.

**Situation:**

Yuki sees the book club is for English and German speakers, but the app description says it translates English ↔ German and English ↔ Japanese. She assumes she can join and communicate in German, but there's no German ↔ Japanese path. She tries anyway and either gets no translation or gets routed through English (a language she doesn't speak).

**Need:**

As Yuki, I want the app to be honest about which language pairs work, so that I don't waste time setting up an account only to discover I can't talk to half the group.

**Acceptance:**
- During signup or profile creation, Yuki selects her language(s) and sees which other languages she can message — not a generic list but a personalized one
- If Yuki picks German, she sees 'you can message English speakers (translated to/from German). You cannot directly message Japanese speakers at v1. They would receive your German message translated to English, not Japanese.'
- The app doesn't silently route German → English → Japanese and pretend it worked

**Tier:** core

**Confusion-flags:**
- This story might be pushing scope — it's really about transparent constraints, not feature request. But I think Sarah and Marcus will hit frustration if the app allows Yuki to join and then silently fails to translate to/from her language pair. The confusion-flag is whether this belongs in v1 or is a fast-follow (better error messaging).
- I don't know what 'message [language] speaker' means technically — is it a dropdown at compose time, a profile setting, or inferred from the recipient's profile? That's the team's job. I just know Yuki needs to know before investing time.
