## Scenario: Empty body ('') and omitted body both default to '' and produce same revision_id

**Severity:** silent-wrongness

**Setup:**

Contract specifies: body is always a string, never null (per contract-note and model invariants).

Two ways to create a note with empty body:
1. POST /api/notes with {title: 'Note 1', body: ''} (explicitly empty)
2. POST /api/notes with {title: 'Note 2'} (body omitted, should default to '')

**Trigger:**

(1) Fetch note 1, compute revision_id='hash_A'.
(2) Fetch note 2, compute revision_id='hash_B'.

**Expected:**

hash_A == hash_B. Both notes have body='', so they have identical state. Their revision_ids must be identical.

**Concern:**

If the hash computation treats empty string ('') and null differently, or if one code path preserves '' and another converts to null, then two notes with equivalent content (both empty body, same title, same tags) will have different revision_ids.

This causes **silent-wrongness** when comparing revisions:
- User edits a note (adds some body), saves (revision_id changes).
- User clears the body (deletes all text), tries to save.
- System compares: "my revision_id is hash_A (when body was empty), but server says hash_B (after my first save with content). Collision!"
- User is confused: "I just cleared the text, why is that a collision?"

Additionally, if null slips into the database for body (violating the NOT NULL constraint), the note becomes corrupted and unfetchable (if the API tries to compute revision_id and encounters null).

**Property:**

For all notes, body is always a string (never null). If body is empty, it is represented as '' (zero-length string).

Two notes with identical title, identical sorted_tag_ids, identical updated_at, and identical body (both '') have identical revision_id.

Formally:
```
hash(title, body='', tag_ids, updated_at) 
  == hash(title, body='', tag_ids, updated_at)
```

regardless of how the body='' was set (explicit vs. default).

**Implies:**

Implies data validation: ensure body is never null. Either:
- Server-side validation rejects null body on POST/PUT and treats omitted body as ''
- Database NOT NULL constraint on body column (already present in schema)
- Hash computation handles null gracefully (though null should never occur)

Implies test: create two notes (one with body='', one with body omitted) and verify they have identical revision_id.

Implies test: attempt to manually insert a note with body=null into the database (should fail at constraint level), then verify the API gracefully rejects fetching that note or raises an error (not silent corruption).
