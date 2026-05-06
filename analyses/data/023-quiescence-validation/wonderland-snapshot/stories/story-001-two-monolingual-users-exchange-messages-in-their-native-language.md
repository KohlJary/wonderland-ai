## Story 001: Two monolingual users exchange messages in their native language

**Persona:** Maya, 31, Berlin-based English speaker. German passable but uncomfortable for casual chat. She's joined a book club that's mostly German speakers. She wants to participate without the cognitive load of composing in German.

**Situation:**

Maya opens a chat with Klaus, a German-speaking book club member. Klaus speaks no English. They want to discuss the book they just finished — conversational, not formal.

**Need:**

As Maya, I want to type in English and see Klaus's German messages translated to English in the same thread, so that I can follow the conversation without switching languages mentally every few seconds.

**Acceptance:**
- I type a message in English. It appears in the thread as-sent (not yet translated).
- Klaus sees my message translated to German.
- Klaus's German replies appear in the thread. I see them in English, near-real-time.
- The order of messages is preserved — no reordering, no batching delays that break conversational flow.
- I can see which language each message was originally written in (visual marker, not intrusive).

**Tier:** core

**Confusion-flags:**
- I don't know if 'near-real-time' means <1 second, <5 seconds, or < message-latency. That affects UX feel significantly.
- It's unclear who does the translation work — a service call on send, or async after? If async, what does 'Klaus sees my message translated' mean timing-wise?
- I assumed both users are looking at the same message thread. If translation happens on the client side (per viewer), the same message might look different to each of us, which feels subtly wrong.
