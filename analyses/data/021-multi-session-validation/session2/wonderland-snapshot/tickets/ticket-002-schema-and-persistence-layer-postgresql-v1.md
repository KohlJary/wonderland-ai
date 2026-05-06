## Ticket 002: Schema and persistence layer (PostgreSQL v1)

**Sources:** adr:translation-chat-data-model-persistence-translation-service-risk-and-user-identity
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1.5–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:message-send-receive-pipeline
- Blocked by: ticket:user-registration-and-auth-email--password-v1
- Soft: —

**Description:**

Design and implement schema for users, chats, and messages. Create tables: users (id, email, password_hash, created_at), chats (id, created_at, participants), messages (id, chat_id, sender_id, content, translated_content, created_at). Implement basic queries for chat history, message insertion, participant lookup. Assume single-language content storage (translated_content as a separate column) pending ADR decision on persistence strategy. No migration system yet; schema updates by hand in v1.

**Acceptance:**
- Schema created and queryable
- Insertion and retrieval queries work for all three tables
- Indexes exist on chat_id and sender_id for message queries
- Participant lookup returns members of a chat
- Schema matches the ADR's data model assumptions

**Risk:**

ADR names 'persistence' as an open tradeoff (e.g., should translated_content be normalized or denormalized?). If Tweedles negotiate a different storage model during implementation, schema may need revision. Coordinate early.
