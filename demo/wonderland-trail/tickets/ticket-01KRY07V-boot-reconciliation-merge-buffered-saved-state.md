## Ticket 070: Boot reconciliation: merge buffered + saved state

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2G
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-persistent-backup
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.75-1.25 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: save-endpoint-atomic-writes
- Soft: tag-input-component

**Description:**

On app boot, check localStorage for buffered content. Call GET /notes/:id to fetch server state. If both exist, compare timestamps: use server version if newer, buffered if newer. If conflict detected from prior save attempt, surface merge UI (show both versions, let Kohl choose). Merge choice updates localStorage + backend.

**Acceptance:**
- App boot fetches both localStorage and server state
- Newer version is used automatically
- Conflict scenarios surface merge UI to user
- User choice is persisted

**Risk:**

Merge UI UX is undefined — may require Alice input. If Kohl dislikes the conflict presentation, rework loop possible.
