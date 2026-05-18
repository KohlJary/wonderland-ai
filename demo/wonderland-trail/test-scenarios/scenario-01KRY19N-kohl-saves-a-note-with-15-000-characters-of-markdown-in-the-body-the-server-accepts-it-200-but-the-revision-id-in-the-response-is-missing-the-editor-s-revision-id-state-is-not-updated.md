## Scenario 263: Kohl saves a note with 15,000 characters of markdown in the body; the server accepts it (200), but the revision_id in the response is missing—the editor's revision_id state is not updated

**GUID:** 01KRY19NJ0GS53FVHNDWBCBT8E
**Severity:** silent-wrongness

**Setup:**

Kohl has edited a note with a very long body (15,000 characters, many code blocks and lists). The keystroke buffer has this large body. She clicks Save.

**Trigger:**

The PUT request is sent. The server processes it successfully, writes the note to SQLite, and returns 200. However, the response body is missing the expected 'revision_id' field (e.g., response is {id, title, body, tags} but no revision_id).

**Expected:**

The frontend should detect the missing revision_id in the success response and either (a) handle it gracefully by treating the save as a partial success (show success message, but leave the editor in a known state with the old revision_id or by fetching the note fresh), or (b) log a warning that the response schema was invalid and suggest the user verify the note was saved by reloading.

**Concern:**

If the frontend assumes revision_id is always present in a 200 response and tries to assign `newRevisionId = response.revision_id` without checking, it will assign `undefined` to the component state. On the next save, the frontend will send revision_id: undefined, which the server will reject as invalid. The user will see a confusing error and may think the save failed when it actually succeeded.

**Property:**

For all successful save responses (200/201), the frontend must validate that the response includes the expected fields (revision_id, id, updated_at, etc.). If a required field is missing, the frontend must handle it as a protocol error, not a success.

**Implies:**
- Implies response schema validation in the save handler.
- Implies a recovery path if the response is malformed but the save probably succeeded (e.g., 'Save may have succeeded, but the server response was invalid; please reload to verify').
