## Scenario 360: Kohl clicks Save with keystroke buffer in localStorage; revision_id is returned and cached

**GUID:** 01KRY1F5JJWC63TXB9SQCCBZWF
**Severity:** breakage

**Setup:**

Kohl has typed a title and body into the editor. The keystroke buffer in localStorage contains {title, body, tag_names}. She clicks the Save button. The client sends POST /api/notes with the current state.

**Trigger:**

The backend responds 200 OK with {id, title, body, tag_names, tag_ids, created_at, updated_at, revision_id}.

**Expected:**

The client receives the response, extracts revision_id, and caches it in editor state (EditorState.revisionId). The localStorage keystroke buffer is cleared (since Save succeeded). The note's id is stored so future saves use PATCH, not POST. If the user immediately closes the browser after Save, reopens the editor on the same note, the editor loads via GET /api/notes/{id}, receives the revision_id from that response, and caches it for the next Save attempt.

**Concern:**

If revision_id is not returned in the POST response, or if the client fails to cache it, the next Save attempt cannot include If-Match header, and collision detection is broken. Multi-tab overwrites become possible without warning.

**Property:**

revision_id is returned on POST and cached for collision detection
