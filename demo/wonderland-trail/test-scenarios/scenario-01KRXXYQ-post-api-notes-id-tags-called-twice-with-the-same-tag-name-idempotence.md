## Scenario 165: POST /api/notes/{id}/tags called twice with the same tag_name (idempotence)

**GUID:** 01KRXXYQD08R1GFPSWEN11326Y
**Severity:** degradation

**Setup:**

A note with no tags. Two sequential requests: POST /api/notes/{id}/tags with tag_name='research' twice.

**Trigger:**

First POST creates and associates the tag. Second POST tries to associate the same tag (should be no-op).

**Expected:**

Idempotent: the tag appears once. Both requests return 200 with the same tag list.

**Concern:**

The code checks 'if tag not in note.tags' before appending. Each request gets a new Session instance (FastAPI dependency per-request). The second request's session loads the note and its relationship from the DB, finds the tag exists, and the check works. This should be idempotent, but SQLAlchemy relationship loading under request-per-session is worth verifying.

**Property:**

POST /api/notes/{id}/tags is idempotent: calling twice with the same tag_name produces identical results to calling once.
