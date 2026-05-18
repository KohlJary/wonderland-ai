## Scenario 267: User in Tab A and Tab B both edit the same note, Tab B saves first, Tab A's save attempt returns 409 with server state

**GUID:** 01KRY19VMP015JW631HNJ74GC1
**Severity:** breakage

**Setup:**

Note #1 exists with title='Experiment notes' body='Initial draft' revision_id_before=hash(title, body, tags, updated_at). User opens the note in Tab A and Tab B. Tab B makes edits (title → 'Experiment notes - REVISED', body → 'Tab B edits'). Tab A independently edits title → 'Experiment notes - revised by A', body → 'Tab A edits'.

**Trigger:**

Tab B submits PUT /notes/1 with If-Match: <revision_id_before> and the Tab B edits. Backend processes successfully. Then Tab A submits PUT /notes/1 with If-Match: <same revision_id_before> and the Tab A edits.

**Expected:**

Tab B's save returns 200 with a new revision_id_B. Tab A's save returns 409 Conflict with the server's current state (Tab B's version) and the server's revision_id_B, WITHOUT modifying the note. The note now contains Tab B's edits, not Tab A's.

**Concern:**

The endpoint currently doesn't validate If-Match headers at all. If Tab A's PUT arrives first, it will succeed. If Tab B's PUT arrives second, it will silently overwrite Tab A's edits because the code just updates all fields, no collision check. This is the silent-wrongness failure mode: both users believe their edits saved, but one of them is actually lost.

**Property:**

For all concurrent save attempts to the same note with different client revision_ids, exactly one succeeds with 200 and returns the new server revision_id; all others fail with 409 and receive the winning server state. No concurrent save ever overwrites an older save without the client explicitly knowing about the collision.

**Implies:**
- Requires If-Match header validation on PUT /api/notes/{id} — flag for Tweedledum.
- Requires revision_id computation (SHA256 hash of [title, body, sorted_tag_ids, updated_at]) on every save response — flag for Tweedledum.
- Requires audit trail logging of both successful saves and conflict attempts — flag for Tweedledum.
- Frontend expects to receive 409 with server state and revision_id; if backend doesn't send it, collision resolution UX fails — flag for Tweedledee.
