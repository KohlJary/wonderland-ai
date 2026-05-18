## Ticket 073: Backend tag CRUD routes (POST, GET, DELETE)

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2K
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-tag-crud-backend
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: tag-browsing-query-endpoint
- Blocked by: schema-tag-table
- Soft: —

**Description:**

Implement POST /tags (create), GET /tags (list all), DELETE /tags/:id (remove). Tags are user-scoped (each user has their own tag namespace). Endpoints return tag id, name, created_at, usage_count. No auth checks needed yet (assume authenticated context).

**Acceptance:**
- POST /tags creates a new tag and returns id + metadata
- GET /tags lists all tags for the authenticated user
- DELETE /tags/:id removes the tag
- Tag operations are user-scoped

**Risk:**

Moderate. Tag cleanup (orphaned tags after note delete) is undefined. Recommend clarifying cascade behavior before starting.
