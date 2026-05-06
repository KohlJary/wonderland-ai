## Story 002: Conversation is persistent and both users see the full history

**Persona:** Klaus, 41, Munich-based, native German speaker. Works in tech, uses chat as the primary record of decisions. Needs to scroll back to context.

**Situation:**

Klaus and Sarah have been messaging for 15 minutes. Klaus needs to scroll back to the start of the conversation to check what they agreed on. He wants the full history visible in both German and English as context.

**Need:**

As Klaus, I want to see the full message history of my conversation with Sarah, with each message showing both the original language and the translation, so that I can refer back to what we agreed without losing context to language switching.

**Acceptance:**
- Klaus can see all prior messages in the conversation, with timestamps in reverse chronological order (newest first, or grouped by time)
- Each message shows: sender name, timestamp, original text (in the sender's language), translated text (in Klaus's language)
- Klaus can scroll freely through the history without pagination friction
- The conversation persists across browser sessions (Klaus closes the tab, comes back later, sees the same messages)

**Tier:** core

**Confusion-flags:**
- What's the visual layout? Does Klaus see a side-by-side (English | German) or stacked (English, then German below) display? The directive doesn't specify, and this affects how quickly he can scan.
- Is there a 'load older messages' boundary, or does every message ever sent appear? If infinite history, does it get slow? Not specified.
- Does Klaus see Sarah's original English text, or only the German translation? If only German, he can't tell if a translation was lossy.
