## Ticket 001: User model with language capability schema

**Sources:** adr: user-language-capability-model-message-translation-surface, story: new-user-joins-and-authenticates-for-the-first-time
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1-1.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: conversation-model-with-language-pair, message-model-with-translation-surface
- Blocked by: —
- Soft: —

**Description:**

Define User(id, username, password_hash, created_at, deleted_at) with soft-delete for GDPR erasure. Language capabilities are implicit via Conversation.language_pair, not stored on User. Includes migration from skeleton code if schema exists; otherwise new schema. No auth enforcement yet (separate ticket).

**Acceptance:**
- User table exists with id, username, password_hash, created_at, deleted_at
- Soft-delete query works (WHERE deleted_at IS NULL filters active users)
- Migration script runs cleanly on skeleton code schema

**Risk:**

Skeleton code may have existing User schema incompatible with soft-delete. If so, expand to 2 days for schema reconciliation.
