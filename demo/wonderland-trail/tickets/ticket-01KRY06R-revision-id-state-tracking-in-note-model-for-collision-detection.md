## Ticket 067: revision ID state tracking in note model for collision detection

**GUID:** 01KRY06RWJVEFDZG541GV8WNBZ
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01HNQ8X2PHQBNK3R8GYV7ZQMSE:kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01KRXZM1NPKFYDBZHDA4GRTS50:frontend-revision-id-tracking-and-collision-detection-flow-integration
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5-1 day, 85% confident
**Status:** open

**Dependencies:**
- Blocks: save-button-integration-with-backend, frontend-load-on-boot-and-merge
- Blocked by: —
- Soft: —

**Description:**

Update the frontend's Note type/schema to include a revision_id field (string, nullable for new notes). Ensure revision_id is populated when notes are loaded from the backend (via GET /notes) or when they're created fresh in localStorage. Revision_id is included in Save requests (ticket: save-button-integration) and is updated after successful saves. This ticket owns the state structure; the actual save/load logic is in the other frontend tickets.

**Acceptance:**
- Note type/interface in the frontend includes a revision_id field (string | null)
- When a note is loaded from the backend, revision_id is extracted and stored
- When a note is created fresh in the editor (no backend entry yet), revision_id is null or undefined
- Before Save, revision_id is included in the request payload (or null if new note)
- After successful Save, revision_id is updated to the new one from the response
- No validation of revision_id format (treat as opaque string); backend is responsible for format/correctness
- TypeScript compilation succeeds with no revision_id-related type errors

**Risk:**

Low — this is mostly schema work. The risk is in how revision_id is passed around and updated in other tickets (save, load, merge). Recommend integrating this ticket early and reviewing with other frontend tickets to ensure consistency.
