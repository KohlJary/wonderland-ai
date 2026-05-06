## Story 001: German professional exchanges technical questions with English peer in real time

**Persona:** Klaus, 42, Munich-based software architect. Native German speaker, fluent in English but prefers to think in German. He is on a distributed team with an English-speaking tech lead in London. He wants to ask architectural questions without the friction of context-switching languages.

**Situation:**

Klaus is in a synchronous design discussion with his English colleague about a system redesign. Both are online, both need to respond quickly. Klaus's English is good but thinking in real time in a non-native language is exhausting. He keeps losing his train of thought mid-sentence.

**Need:**

As Klaus, I want to type my questions and observations in German and see them translated to English in real time, so that I can think at full speed and my colleague gets my actual meaning without the lag of manual translation.

**Acceptance:**
- Klaus types a German message; it appears in his chat window as German
- Within 2–3 seconds, the message translates to English and appears in his colleague's window
- Klaus can see that his message was sent and is being read; he does not have to wonder if the connection broke
- The English version is natural English, not awkward machine translation (he can judge this; he's fluent)
- If translation fails, Klaus sees a clear error message, not a hung state

**Tier:** core

**Confusion-flags:**
- The skeleton has an /api/messages echo endpoint that just bounces text back. Real translation chat needs to call a translation service (Google Translate? DeepL?). This isn't wired yet. Where does that live?
- I don't know whether Klaus's message should show him the German original or the English translation first. Real-time translation UI has UX choices baked in — which one is right? Should it be configurable?
- What happens if the translation service is slow? Does Klaus's message appear instantly and then the translation arrives async? Or does everything hang until translation completes? The skeleton doesn't show error-state or loading-state handling.
- GDPR applies to these messages. Klaus's German text is personal data; so is the English translation. Does the backend store both? For how long? The skeleton doesn't show a retention policy.
