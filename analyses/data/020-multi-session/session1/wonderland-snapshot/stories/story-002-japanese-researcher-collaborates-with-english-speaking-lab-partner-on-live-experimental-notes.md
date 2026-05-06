## Story 002: Japanese researcher collaborates with English-speaking lab partner on live experimental notes

**Persona:** Yuki, 28, Tokyo-based molecular biologist. Native Japanese speaker, reads English journals fluently but speaking/typing English under time pressure is difficult. She is collaborating with a U.S.-based lab partner on a multi-year project. They need to document observations in real time while the experiment is running.

**Situation:**

Yuki and her partner are running a time-sensitive experiment. They are documenting observations, asking clarifying questions, sharing hypotheses as data comes in. They are both stressed. The experiment lasts 4 hours. They need to stay synchronized without language becoming a bottleneck.

**Need:**

As Yuki, I want to type observations and questions in Japanese without waiting for manual translation, so that I can keep pace with the experiment's rhythm and my partner can understand my actual reasoning, not a delayed summary.

**Acceptance:**
- Yuki types a Japanese message about what she is observing; it appears in the chat window within 3 seconds with an English translation visible to her partner
- Her partner can see both the timestamp and the fact that a message has arrived; message ordering is clear (no out-of-sequence confusion)
- If Yuki's network drops mid-message, the message either sends completely or fails cleanly — no partial messages in the chat
- The translation is scientific English, not colloquial (Yuki is using technical terms; they need to translate correctly)
- After the experiment, both Yuki and her partner can export the chat history for their lab notes

**Tier:** core

**Confusion-flags:**
- English ↔ Japanese translation is harder than English ↔ German. Grammatical structures are further apart. I don't know if a basic translation API will produce acceptable quality. Should there be a human review step for scientific data? Or is this a fast-follow?
- Yuki is on a 4-hour time-critical task. If the chat UI is clunky or slow, it breaks her focus. What is the latency budget? What is the UI responsiveness requirement? The skeleton doesn't show performance targets.
- The MVP says 'basic auth' — but Yuki's experiment data is sensitive. Does she need end-to-end encryption? GDPR has rules about data in transit. The skeleton doesn't show security consideration.
- Message history: does Yuki need to see her previous chats? Can she search them? The skeleton is an echo endpoint — history is missing. Is that in scope for MVP?
