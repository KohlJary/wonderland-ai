## Story 006: System operator verifies block enforcement without data leakage

**Persona:** Sam, 28, a DevOps operator responsible for the translation-chat backend. A user (Maya) reports that blocking is not working — she blocked someone but she is still seeing their messages. Sam needs to debug this without being able to read the actual message content (GDPR: user conversations are private; Sam can see structure and logs, not content).

**Situation:**

Maya reports a block failure via support. Sam logs into an admin surface and needs to verify: (1) the block was created, (2) the block is being enforced in the message-fetch logic, (3) if there's a bug, the bug is in the blocking logic, not in the translation or message storage. Sam has access to user IDs, conversation IDs, message counts, but not message text.

**Need:**

As Sam, I want to query the block relationship between two users and verify that message-fetch queries respect the block, without ever seeing message content or reading private conversation data.

**Acceptance:**
- Sam can query 'is user X blocked by user Y' and see a boolean result
- Sam can query 'how many messages in conversation C are hidden from user X due to blocks' and see a count
- Sam can see a message's metadata (created_at, sender_id, receiver_id, translation_status) without seeing the text
- Sam can verify that a GET /conversations/{id}/messages query for user X returns N messages, and a GET /conversations/{id}/messages/all query (admin view) returns N + M messages (where M is the count of blocked-user messages), confirming blocks are enforced
- Sam cannot accidentally read message content while debugging block logic

**Tier:** core

**Confusion-flags:**
- The distinction between 'an admin endpoint that bypasses blocks for debugging' and 'an admin endpoint that respects blocks and only shows metadata' is critical and I don't know which the team intends. If Sam can see all messages including blocked ones, he can read private content. If he cannot, he has limited visibility into what users are reporting. This is a compliance boundary that needs explicit decision.
- The phrase 'without ever seeing message content' is strong. Does it apply only to the blocking-debug surface, or to all admin surfaces Sam accesses? If Sam can see message content in other admin queries, the bound is weaker than I'm stating here. Accepting this as a boundary that needs clarification.
