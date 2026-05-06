## Story 006: Block a user who is bothering me

**Persona:** Sarah, 28, a German therapist facilitating peer support groups across language barriers. She joined the chat to connect clients in her home group with Spanish-speaking colleagues. A person in a test group has started sending unwanted personal messages.

**Situation:**

Sarah is exchanging legitimate work messages with her peers when she receives messages from someone who is not part of her professional network. The messages are persistent and crossing personal boundaries. She needs to stop seeing them and prevent further contact.

**Need:**

As Sarah, I want to block this person so that they can no longer send me messages and I can no longer see our conversation history.

**Acceptance:**
- After blocking, Sarah does not see any messages from the blocked person in her conversation list
- The blocked person's messages are not delivered to Sarah (they receive no 'sent' confirmation that the message reached Sarah)
- Sarah can see that a person is blocked (somewhere in the UI, she knows the state is active)
- Sarah can unblock the person later if circumstances change

**Tier:** core

**Confusion-flags:**
- The spec says 'bidirectional in visibility, not symmetric in initiation' — this means Sarah blocked them and they can't see her messages either, but only Sarah initiated the block. This feels right for safety, but I want to confirm: does the blocked person know they're blocked, or do they just see messages disappearing into the void? That's a UX question that might matter for Sarah's sense of whether the block is working.
- Blocking is permanent (until unblock) but messages are deleted on GDPR timelines — what happens if the GDPR retention period expires before Sarah unblocks? Does the block persist as a rule even though there are no messages to hide?
