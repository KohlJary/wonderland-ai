## Story 005: User sees their own conversation list and can pick which one to read

**Persona:** Klaus (same as above), after multiple conversations. Klaus has been chatting with Sarah and also with Michael (English speaker). He lands on the app and wants to see at a glance who he's been messaging.

**Situation:**

Klaus opens the app. He's logged in. He wants to see a list of his active conversations (with Sarah, with Michael, etc.) and click to open any of them.

**Need:**

As Klaus, I want to see a list of all my conversations with a preview of the last message and who I'm talking to, so that I can quickly jump to the conversation I need.

**Acceptance:**
- Klaus sees a conversation list when he logs in
- Each conversation shows: the other user's name/handle, a timestamp of the last message, a preview of the last message (first 40-50 chars)
- Klaus can click on a conversation to open it and see the full history
- The list is sortable by recency (most recent first, default)
- Klaus can see an unread-message count or indicator if messages have arrived since he last read a conversation

**Tier:** core

**Confusion-flags:**
- What if Klaus wants to start a fresh conversation with someone he's talked to before? Does he create a 'new chat', or does re-opening their conversation resume the old thread? I'm assuming resume, but it's not specified.
- Unread count — is this a nice-to-have or essential? I've marked it as acceptance because it's a standard UX pattern for chat, but if the directive says MVP is minimal, this might be fast-follow.
- Search within conversations — is that in scope? Probably not v1. Flagging.
