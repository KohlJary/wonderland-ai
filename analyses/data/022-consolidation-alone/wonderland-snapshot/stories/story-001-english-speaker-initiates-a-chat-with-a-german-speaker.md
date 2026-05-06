## Story 001: English speaker initiates a chat with a German speaker

**Persona:** Sarah, 34, Berlin-based English expat, native speaker. Works in tech, uses chat for quick team collaboration across language boundaries. Impatient with friction.

**Situation:**

Sarah wants to message Klaus, a German colleague, about a project decision. Klaus is fluent in English but prefers German for nuance. Sarah wants to write in English and know Klaus sees her intent clearly, even across the language boundary.

**Need:**

As Sarah, I want to start a conversation with Klaus and send him a message in English, seeing it translate to German in real-time, so that we can communicate without either of us having to code-switch.

**Acceptance:**
- Sarah can initiate a new chat with Klaus (identified by user handle or email)
- Sarah can type a message in English and send it
- Klaus receives the message in German translation within 1-2 seconds of send
- Sarah sees her own message in English in her view; Klaus sees it in German in his view
- Both see a timestamp and sender identity for each message

**Tier:** core

**Confusion-flags:**
- How does Sarah 'identify' Klaus? Is there a user directory, or does she need his exact handle? The directive says 'two users' but doesn't specify discovery/pairing.
- What happens if the translation is poor or ambiguous? No error state is specified. Does Sarah see [Translation uncertain] or just accept it?
- Does Sarah see that her message was translated, or is it transparent? If transparent, does she trust it?
