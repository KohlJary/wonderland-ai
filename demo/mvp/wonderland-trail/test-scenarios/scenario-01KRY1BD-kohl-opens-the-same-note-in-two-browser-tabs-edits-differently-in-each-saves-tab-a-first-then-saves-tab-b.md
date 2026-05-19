## Scenario 306: Kohl opens the same note in two browser tabs, edits differently in each, saves Tab A first, then saves Tab B

**GUID:** 01KRY1BD9QYCM0QJV0RZ20601E
**Severity:** breakage

**Setup:**

Kohl has note ID 42 open in Tab A (title='Research Protocol', revision_id='v1'). She makes an edit: changes title to 'Research Protocol - Draft 2'. She saves in Tab A. Server returns 201 with revision_id='v2'. Meanwhile, Tab B has the same note (revision_id='v1' cached locally from its load), and Kohl changes body to 'New findings...' without saving yet.

**Trigger:**

Kohl clicks Save in Tab B. Frontend sends PUT /api/notes/42 with If-Match: 'v1', but the server's current revision_id is 'v2'.

**Expected:**

Server returns 409 Conflict with {error: 'ConflictError', server_revision_id: 'v2', server_state: {id: 42, title: 'Research Protocol - Draft 2', body: <old_body>, ...}}. Tab B's editor displays a collision warning: 'Another tab saved changes. Your edits are [preview]. Would you like to: (a) Keep my edits, (b) Load server version?' Kohl chooses; no silent overwrite occurs.

**Concern:**

If the 409 response is not returned (endpoint silently overwrites Tab A's save with Tab B's edits), Kohl loses Tab A's work. If the collision response doesn't include the server state, Kohl can't make an informed choice about which version to keep. If the warning is unclear, Kohl overwrites her own work accidentally.

**Property:**

Multi-tab collision detection + safe conflict presentation
