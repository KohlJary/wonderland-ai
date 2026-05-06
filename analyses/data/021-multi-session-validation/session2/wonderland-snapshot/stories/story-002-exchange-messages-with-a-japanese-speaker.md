## Story 002: Exchange messages with a Japanese speaker

**Persona:** Akira, 34, based in Tokyo, English learner, wants to practice conversation with native speakers but hasn't gotten comfortable enough to join an all-English community. Uses translation tools for work email but wants the chat to feel more conversational.

**Situation:**

Akira found a hobby community online but it's English-dominant. He's been lurking for months. He wants to contribute but knows his English would be slow and imperfect. A translator-augmented chat would lower the barrier.

**Need:**

As Akira, I want to chat with English speakers in Japanese and read their responses translated to Japanese, so that I can participate in a community I'm interested in without the friction of composing in a non-native language.

**Acceptance:**
- Akira types a message in Japanese and sends it.
- The message appears in the chat in both Japanese and English.
- An English speaker receives the English translation immediately.
- An English speaker's reply comes back with Japanese translation Akira can read.
- The flow doesn't feel slow or laggy — responses feel near-real-time.
- Akira can see the original English if he wants to check his understanding.

**Tier:** core

**Confusion-flags:**
- Japanese character encoding and display — I assume the frontend handles UTF-8, but I haven't checked the skeleton. Is that already there or a blocker?
- Same GDPR questions as the German case — does this shape the MVP or come after?
- Is 'near-real-time' actually real-time or is latency acceptable? The directive says 'near-real-time translation' but I don't know what the SLA is.
