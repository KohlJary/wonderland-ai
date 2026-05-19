## Scenario 064: Kohl edits an existing note's title and body, clicks Save, and the changes persist across page reload

**GUID:** 01KRXTE35W88GEZR30A8W5VQ4C
**Severity:** silent-wrongness

**Setup:**

A note with id=1, title='Old title', body='Old body' exists on the server. Kohl has opened it in the editor (via previous save or fetch)

**Trigger:**

Kohl changes title to 'New title', changes body to 'New body with more detail', clicks Save

**Expected:**

The PUT /api/notes/1 succeeds with 200. The response includes the updated title, body, and an updated_at timestamp that is newer than the previous value. When Kohl reloads, the note shows the new title and body

**Concern:**

If the title is not updated, or if updated_at is not refreshed, Kohl will not know her edits took effect. Silent data loss

**Property:**

Server updates both title and body atomically; updated_at is refreshed; created_at is immutable

**Implies:**
- PUT /api/notes/{id} request body matches contract
- Response includes updated_at with newer timestamp than previous version
- created_at is unchanged
