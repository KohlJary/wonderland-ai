## Ticket 064: GET /notes endpoint and boot-time merge reconciliation

**GUID:** 01KRY06RWJVEFDZG541GV8WNBW
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01HNQ8X2PHQBNK3R8GYV7ZQMSE:kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01KRXZJRZ7SWB69XK08PXVYNEY:load-endpoint-fetches-notes-from-sqlite-with-merge-strategy-for-localstorage-drift
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5-2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-load-on-boot-and-merge
- Blocked by: backend-note-model-and-atomic-save-endpoint
- Soft: —

**Description:**

Implement GET /notes endpoint that returns all persisted notes for the single operator with full state (title, body, tags, created_at, updated_at, revision_id). Response is ordered by updated_at descending. The frontend will call this on boot and merge the persisted notes with localStorage keystroke buffers, using revision_id as the reconciliation key. This ticket owns only the backend endpoint; the frontend merge logic is a separate ticket.

**Acceptance:**
- GET /notes returns array of all notes (for v1 single operator) in JSON format
- Each note in the response includes: id, title, body, tags, created_at, updated_at, revision_id
- Response is ordered by updated_at DESC (most recently modified first)
- Response is fast for ~100 notes (<100ms) — no N+1 queries, efficient serialization
- GET /notes/{id} returns a single note by id with the same schema (optional, but useful for fetch-one scenarios)
- If no notes exist, GET /notes returns an empty array (not an error)

**Risk:**

If tags are serialized inefficiently or the query does a join per tag, response time could degrade with note count. Recommend using SQLite's JSON functions or a pre-computed tags array in the response to avoid join cost.
