## Scenario 266: Kohl saves a note, the server returns 200, the revision_id in the response is identical to the revision_id Kohl sent—the server did not update the note (idempotent save, or bug?)

**GUID:** 01KRY19NJ0GS53FVHNDWBCBT8H
**Severity:** curiosity

**Setup:**

Kohl saves a note with revision_id 'rev_5'. The server processes the request. However, due to a bug or a deduplication feature, the server doesn't actually update the note (content is identical to what's already saved). The server returns 200 with revision_id 'rev_5' (unchanged).

**Trigger:**

The frontend receives the 200 response with revision_id 'rev_5'. It updates the local revision_id to 'rev_5' (no-op, it's the same). The UI shows a success message.

**Expected:**

The success message is shown, and the editor remains in sync with the backend (no collision, because the note state on the backend matches the frontend's state). If the server genuinely didn't update the note, this is harmless (idempotent save). If the server intended to update but failed silently, this is a problem on the backend, not the frontend.

**Concern:**

The frontend cannot distinguish between 'server didn't change anything because the content was identical' (idempotent, OK) and 'server intended to save but encountered an error and returned 200 anyway' (bug, bad). The frontend's correct behavior is to trust the 200 response and the returned revision_id as canonical. If the backend has a bug, that's a backend defect, not a frontend one.

**Property:**

If the server returns 200, the frontend treats the response revision_id as canonical, regardless of whether it changed.
