## Ticket 075: Tag browsing query endpoint (GET /tags/:tag_id/notes)

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2N
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-tag-browsing
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5-0.75 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: tag-crud-routes
- Soft: —

**Description:**

Implement GET /tags/:tag_id/notes. Returns list of all notes tagged with that tag, user-scoped. Response includes note id, title, preview, last_modified. Paginate if needed.

**Acceptance:**
- GET /tags/:tag_id/notes returns notes for the tag
- Results are user-scoped
- Response includes note metadata

**Risk:**

Low.
