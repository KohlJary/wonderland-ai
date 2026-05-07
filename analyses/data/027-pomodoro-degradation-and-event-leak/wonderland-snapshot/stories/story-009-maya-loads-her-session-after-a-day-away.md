## Story 009: Maya loads her session after a day away

**Persona:** Maya, 31, polyglot book-club moderator. She juggles three languages across two devices (phone, desktop). She opens the app expecting to see exactly what she left.

**Situation:**

Maya is reading a book discussion in German and Japanese simultaneously across a Discord server and a WhatsApp group. She closes the app on her phone after an hour of moderating. The next evening, she opens her phone again to catch up on the thread.

**Need:**

As Maya, I want my session—the exact state of which language pairs I was viewing, which messages I had marked, which settings I had active—to be restored exactly as I left it, so that I can pick up moderating without re-orienting.

**Acceptance:**
- Session opens to the same view (language pair, scroll position, marked messages) as when closed
- Settings (font size, dark mode, notification preferences) are preserved from the last action
- No data loss: marked messages remain marked; conversation history is intact
- Restoration happens within 2 seconds of app launch

**Tier:** core

**Confusion-flags:**
- What happens if Maya's *other device* (desktop) modified the session while her phone was closed? Do we show her a conflict, merge silently, or use last-write-wins? This affects whether she sees a notification or not—a UX boundary.
- Does 'restore exactly' mean the language pairs she had open, or does it also mean the exact order/grouping? If she added a new pair on desktop while phone was closed, does the phone see it immediately or on next sync?
- What if the session is deleted server-side between close and reopen (e.g., user's cloud account was reset)? Should she see an error, or does the app silently fall back to defaults?
