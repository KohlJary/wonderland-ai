## Scenario 169: PUT and DELETE race condition on the same note (concurrent mutations)

**GUID:** 01KRXXYQD08R1GFPSWEN113272
**Severity:** breakage

**Setup:**

Two concurrent requests: PUT /api/notes/{id} and DELETE /api/notes/{id} (same note_id).

**Trigger:**

PUT to update arrives at the same moment as DELETE to remove.

**Expected:**

One request succeeds, the other fails with 404. Database state is consistent (note either updated or deleted, never partially).

**Concern:**

Both requests get separate SQLAlchemy Session instances. SQLite's serializable isolation should prevent interleaving. Behavior should be correct, but worth verifying under load.

**Property:**

All mutations are atomic and isolated; concurrent mutations on the same note either succeed independently or one fails with 404.
