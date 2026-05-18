## Scenario 347: Client sends If-Match header with stale revision_id, server has a newer version, PUT returns 409 Conflict without updating the note

**GUID:** 01KRY1DY1PSMHZM094C8W7E46M
**Severity:** breakage

**Setup:**

Note id=1 starts with revision_id='hash_old'. Tab A loads and caches 'hash_old'. Meanwhile, Tab B edits and saves, changing the note. Backend now has revision_id='hash_new'.

**Trigger:**

Tab A sends PUT /notes/1 with If-Match: hash_old, request body {title: 'edit_a', body: 'edited by tab a'}.

**Expected:**

PUT returns 409 Conflict with response body including server_revision_id='hash_new' and server_state containing the current note. The note is NOT updated with Tab A's edit.

**Concern:**

This is the core bug collision detection prevents. If PUT succeeds instead of failing, Tab B's changes are silently overwritten.

**Property:**

For all PUT requests where If-Match revision_id does not match the current server revision_id, the request fails with 409 and the note is not modified.
