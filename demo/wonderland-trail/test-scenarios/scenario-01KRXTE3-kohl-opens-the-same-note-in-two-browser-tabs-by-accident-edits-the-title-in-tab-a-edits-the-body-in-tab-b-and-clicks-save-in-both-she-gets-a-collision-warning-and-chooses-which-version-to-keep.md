## Scenario 068: Kohl opens the same note in two browser tabs by accident, edits the title in Tab A, edits the body in Tab B, and clicks Save in both; she gets a collision warning and chooses which version to keep

**GUID:** 01KRXTE35W88GEZR30A8W5VQ4G
**Severity:** silent-wrongness

**Setup:**

Note id=1 with title='Old title', body='Old body' is open in both Tab A and Tab B. Tabs are in separate browser windows or tabs

**Trigger:**

Tab A: Kohl changes title to 'Tab A title', clicks Save (succeeds, 200). Tab B: Kohl changes body to 'Tab B body', clicks Save

**Expected:**

Tab B's Save request includes an If-Match header with the version from the last fetch (the 'Old body' version). Server detects that the note has been modified (Tab A's save updated it), returns 409 Conflict with server_state. Tab B's UI shows a collision warning: 'This note was modified in another tab. Your changes: [show Tab B body]. Server version: [show Tab A title + old body]. Keep your changes or reload?' Kohl chooses 'Keep mine' or 'Reload', and the choice is handled correctly

**Concern:**

If collisions are not detected, Tab B's Save silently overwrites Tab A's title with the old title from when Tab B last loaded. Kohl loses work without knowing it. If the warning is shown but the choice is not implemented, Kohl is trapped

**Property:**

Concurrent writes from different tabs are detected; user is offered explicit choice

**Implies:**
- Frontend tracks note version (revision number or ETag) in state
- PUT /api/notes/{id} includes If-Match header with current version
- Server returns 409 Conflict if version mismatch, with server_state in response
- Frontend detects 409, shows collision UI, and handles user choice (overwrite or reload)
