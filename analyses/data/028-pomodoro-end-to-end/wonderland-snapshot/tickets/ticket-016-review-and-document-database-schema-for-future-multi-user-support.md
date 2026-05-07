## Ticket 016: Review and document database schema for future multi-user support

**Sources:** understand-the-database-schema-for-future-multi-user-support
**Owner:** tweedledum
**Tier:** fast-follow
**Estimate:** 1–2 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

Document the current single-user database schema. Identify what would need to change to support multiple users in the future (e.g., adding user_id foreign keys, partitioning session records by user, auth/login tables). Do not implement multi-user support yet—just document the path so a future ticket can follow it cleanly.

**Acceptance:**
- Current schema is documented in a design document or README
- Multi-user schema changes are identified and described
- Migration path is outlined (e.g., add user_id, backfill, add unique constraints)
- Document is stored in the repo for future reference

**Risk:**

Schema design choices made now (e.g., how sessions are keyed) could constrain multi-user migration; careful design now pays dividends later.
