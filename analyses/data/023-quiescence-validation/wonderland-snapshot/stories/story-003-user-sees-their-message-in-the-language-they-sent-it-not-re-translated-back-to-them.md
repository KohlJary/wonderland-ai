## Story 003: User sees their message in the language they sent it, not re-translated back to them

**Persona:** Klaus, 45, Munich. Native German speaker, reads English slowly. He's in a book club chat with Maya (English speaker). He wants to know his message came through.

**Situation:**

Klaus hits send on his German message. He wants to see confirmation it landed before the translation happens.

**Need:**

As Klaus, I want to see my sent message in German (the language I wrote it in), so that I know exactly what I said before I read the translated version of what the other person sent back.

**Acceptance:**
- When I send a message, I see it immediately in the thread in German (my send language).
- I do not see Klaus's own message re-translated back to German (that would be confusing and pointless).
- I see the other person's original language + translation.

**Tier:** core

**Confusion-flags:**
- This acceptance criteria assumes an asymmetric model: 'I see my sent language, I see their original + translation.' That's cleaner UX than a symmetric 'everyone sees everything translated to their language,' but I'm not sure the backend will support it. The Cat should weigh in on whether this is harder than it sounds.
