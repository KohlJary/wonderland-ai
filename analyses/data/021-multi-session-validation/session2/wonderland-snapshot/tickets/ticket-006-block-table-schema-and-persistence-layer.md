## Ticket 006: Block table schema and persistence layer

**Sources:** story: block-a-user-who-is-bothering-me, story: see-my-list-of-blocked-users, story: unblock-someone-and-resume-contact
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: blocking-endpoints-post-get-delete-blocks
- Blocked by: ticket: schema-and-persistence-layer-postgresql-v1
- Soft: —

**Description:**

Add Block table to schema: (id, blocker_id, blocked_id, created_at). Unique constraint on (blocker_id, blocked_id). Unidirectional semantics: only blocker can unblock. Hard-delete on account deletion of either party. Seed migration script. No ORM changes needed; query logic is handled in endpoints.

**Acceptance:**
- Block table exists with correct schema and uniqueness constraint
- Blocker and blocked_id foreign keys validate correctly
- created_at populated on insert
- Migration script runs without error on existing schema

**Risk:**

If account deletion cascading is complex (e.g., soft-delete semantics elsewhere in the schema), hard-delete may conflict — surface early if present.
