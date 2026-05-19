## Ticket 074: Schema: tags and tag-note association table

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2M
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-tag-schema
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: tag-crud-routes
- Blocked by: —
- Soft: —

**Description:**

Add sqlite tables: tags (id, user_id, name, created_at) and tag_associations (tag_id, note_id, created_at). Ensure unique constraint on (user_id, tag_name). Ensure foreign keys. Run migration script. No API exposure yet.

**Acceptance:**
- tags and tag_associations tables exist in sqlite
- Constraints are enforced
- Migration script is idempotent

**Risk:**

Low.
