## Scenario 311: Kohl edits her saved note in two tabs, saves in tab A, then reloads tab B and sees the most recent version without loss

**GUID:** 01KRY1C0REHH0KMQPVA6ED258F
**Severity:** silent-wrongness

**Setup:**

Kohl has a saved note with id=42, title='Research Notes', updated_at=2026-05-18T10:00:00Z, version='hash-v1' (from prior save). Tab A: user edits the title to 'Final Research' and clicks Save. POST succeeds, returns version='hash-v2'. Tab B: still has the old version in Editor state (version='hash-v1'). Kohl reloads tab B.

**Trigger:**

Tab B mounts. loadNotes() calls GET /notes/42. Response returns the current state: title='Final Research', version='hash-v2'.

**Expected:**

Editor hydrates with title='Final Research'. The version='hash-v2' is cached. When/if Kohl edits in tab B and saves, the PUT request includes If-Match: hash-v2, which matches the server's current version, and the save succeeds.

**Concern:**

If Editor caches the old version='hash-v1' instead of fetching the fresh version from GET /notes/42, subsequent edits in tab B would send If-Match: hash-v1, the server returns 409 Conflict (version mismatch), and Kohl sees an error without understanding why (version='hash-v2' is now on server, but she has no way to know).

**Property:**

Page reload fetches fresh version identifier from backend, preventing stale If-Match headers in subsequent saves.

**Implies:**
- GET /notes/42 response includes version field (current revision_id)
- Editor's useEffect(noteId) fetches fresh note data on mount, updating the cached version
- Collision detection shows a user-facing warning if If-Match fails, not a silent 409 error
