## Ticket 065: save button integration with backend endpoint and collision handling

**GUID:** 01KRY06RWJVEFDZG541GV8WNBX
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01HNQ8X2PHQBNK3R8GYV7ZQMSE:kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01KRXZM1NPKFYDBZHDA4GRTS4Y:frontend-save-button-integration-with-backend-save-endpoint
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5-2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: localStorage-keystroke-buffer, backend-note-model-and-atomic-save-endpoint, frontend-revision-id-tracking
- Soft: —

**Description:**

Implement Save button in the editor that calls PUT /notes/{id} with the current note state (title, body, tags) and revision_id from the last load. Handle 200 success (update local revision_id, show brief success message). Handle 409 Conflict (emit collision warning, offer user choice: keep local edits or load backend version). Handle network error or 5xx (show error, keep Save button enabled for retry). Disable Save button while a request is in flight. localStorage keystroke buffer is NOT cleared after save.

**Acceptance:**
- Save button is visible in the editor and is disabled while a save request is in flight
- Clicking Save calls async PUT /notes/{id} with {title, body, tags, revision_id} payload
- On 200 response, success message is shown briefly (1-2 seconds) and local revision_id is updated to the new one from the response
- On 409 Conflict response, a collision warning modal/toast appears with the backend's newer state; user is offered 'keep my edits' (ignore collision) or 'load backend version' (discard local edits and load remote)
- On network error or 5xx, an error message is shown and Save button remains enabled
- localStorage keystroke buffer is NOT cleared after successful save (Kohl can continue editing after saving)
- Dirty-flag optimization: if no edits have been made since last save, the Save button could be disabled or show 'no changes' — not required but nice-to-have

**Risk:**

409 Collision handling can be confusing for users; the warning message needs to be clear and offer a simple choice. Recommend designing the modal carefully and testing with a user (Kohl) before shipping.
