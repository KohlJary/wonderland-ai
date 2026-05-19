## Scenario 008: Kohl saves multiple notes in sequence — each gets a unique id and no collisions occur

**GUID:** 01KRXSC2B76HKK0C1NK7MRJY5X
**Severity:** breakage

**Setup:**

Kohl has saved two notes successfully: note_id=1 (title='Exp1', body='...') and note_id=2 (title='Exp2', body='...'). She now creates a third note with title='Exp3' and body='...'.

**Trigger:**

Kohl clicks Save on the third note. The backend inserts a new row into the notes table.

**Expected:**

The backend returns a 200 response with {id: 3, title: 'Exp3', body: '...', created_at: '2024-01-15T10:23:45Z', updated_at: '2024-01-15T10:23:45Z'}. The id=3 is unique across all notes. Kohl can later retrieve note 1, note 2, and note 3 independently by their ids without confusion or collision.

**Concern:**

If the schema's id primary key is not auto-incrementing or not enforced as unique, two inserts could generate the same id, causing one note to overwrite another (silent data loss, breakage). If the id generation is collision-prone or relies on client-side assignment, Kohl's notes can collide — this is catastrophic for durability.

**Property:**

Each note insertion generates a globally unique, non-colliding id that is enforced at the database level.

**Implies:**
- id is defined as INTEGER PRIMARY KEY AUTOINCREMENT (SQLite)
- Concurrent inserts do not collide (checked separately in Hatter's scenarios)
- GET /api/notes/{id} retrieves the correct note for each id without mixing data
