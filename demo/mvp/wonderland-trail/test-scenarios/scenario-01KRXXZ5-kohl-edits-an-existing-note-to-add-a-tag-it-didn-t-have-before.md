## Scenario 173: Kohl edits an existing note to add a tag it didn't have before

**GUID:** 01KRXXZ5QRD8WJ7NFN2AZWEHWZ
**Severity:** silent-wrongness

**Setup:**

Note id=1 ('Rust Concurrency Notes') currently has tags=['rust'] (one tag). Kohl opens the editor for this note, sees the tag 'rust' already present, and adds a new tag 'concurrency' to the tag list (now ['rust', 'concurrency']).

**Trigger:**

Kohl clicks Save. The Editor sends PUT /api/notes/1 with {title: 'Rust Concurrency Notes', body: '...', tag_names: ['rust', 'concurrency']}.

**Expected:**

PUT returns 200 with the updated note including both tags: {id: 1, ..., tags: [{id: 42, name: 'rust'}, {id: 43, name: 'concurrency'}]}. Both tags are now associated with the note.

**Concern:**

If the PUT endpoint does not properly replace the tag list (e.g., it only adds new tags and doesn't remove old ones, or it doesn't create new tags if missing), the note would end up with wrong tags. The user sees their save succeed but the tag state diverges from what they sent.

**Property:**

Tag replacement on PUT is atomic and idempotent

**Implies:**
- put-replaces-tag-set-not-appends
- tag-auto-creation-on-update
- response-reflects-full-updated-tag-list
