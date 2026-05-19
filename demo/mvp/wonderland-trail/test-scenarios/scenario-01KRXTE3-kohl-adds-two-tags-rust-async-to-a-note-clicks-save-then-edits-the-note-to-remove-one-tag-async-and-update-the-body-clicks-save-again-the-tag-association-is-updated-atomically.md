## Scenario 066: Kohl adds two tags ('rust', 'async') to a note, clicks Save, then edits the note to remove one tag ('async') and update the body, clicks Save again; the tag association is updated atomically

**GUID:** 01KRXTE35W88GEZR30A8W5VQ4E
**Severity:** silent-wrongness

**Setup:**

A note exists with tag_names: ['rust', 'async']. Kohl opens it in the editor

**Trigger:**

Kohl removes 'async' from the tag list (leaving 'rust'). She edits body. She clicks Save

**Expected:**

PUT /api/notes/{id} with tag_names: ['rust'] succeeds. Response includes tag_names: ['rust'] and tag_ids: [id_of_rust_tag]. The 'async' tag still exists on the server (not deleted, just disassociated from this note). When Kohl reloads, the note shows only 'rust'

**Concern:**

If tag disassociation is not atomic (body updates but tags are not cleared), the note will have stale tags. If the 'async' tag is deleted entirely, other notes using it are broken

**Property:**

Tag associations are updated atomically with note body; tag deletion is not implicit (disassociated tags persist)

**Implies:**
- PUT /api/notes/{id} with tag_names replaces the entire tag association list
- Tags not in the new list are disassociated (DELETE from note_tags), not deleted from tags table
- Response includes tag_ids so frontend can cache for future updates
