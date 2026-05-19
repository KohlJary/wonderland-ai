## Ticket 072: Tag-note association (frontend persistence layer)

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2J
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-tag-input
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5-0.75 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: tag-input-component
- Soft: save-endpoint-atomic-writes

**Description:**

Wire tag input to note state. When note is saved, capture the tag list. On save endpoint call, include tags in the request body. On load, populate tag input from the returned note object.

**Acceptance:**
- Tags are captured when note is saved
- Tags are sent to backend in save request
- Tags are restored from loaded note object

**Risk:**

Low. Depends on save endpoint contract being clear.
