## Story 005: Message delivery and typing indicators (fast-follow; mentioned for completeness)

**Persona:** Same users as above, in any multi-user scenario.

**Situation:**

Users are waiting for messages and wondering if the other person is typing or if the message arrived.

**Need:**

As any user, I want to see that my message was delivered and to see typing indicators from other users, so that the conversation feels live and I am not left wondering if the system is working.

**Acceptance:**
- After I send a message, it shows a 'delivered' or 'sent' state
- I see a typing indicator when another user is composing a message

**Tier:** fast-follow

**Confusion-flags:**
- Typing indicators are nice-to-have, not core. If we ship without them, the experience is still usable but feels less polished.
- Real-time typing indicators + translation creates load questions: do we translate while typing, or only on send? The latter is much simpler.
