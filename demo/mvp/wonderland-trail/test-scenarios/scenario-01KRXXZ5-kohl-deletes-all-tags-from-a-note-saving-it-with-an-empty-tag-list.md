## Scenario 174: Kohl deletes all tags from a note, saving it with an empty tag list

**GUID:** 01KRXXZ5QRD8WJ7NFN2AZWEHX0
**Severity:** silent-wrongness

**Setup:**

Note id=2 ('Experiment Log') currently has tags=['biology', 'lab-procedures']. Kohl opens the editor, removes both tags (tag list is now []). The Note.body still has content.

**Trigger:**

Kohl clicks Save. The Editor sends PUT /api/notes/2 with {title: 'Experiment Log', body: '...', tag_names: []}.

**Expected:**

PUT returns 200 with the updated note: {id: 2, ..., tags: []} (empty array). The note persists but has no tags. A subsequent GET /api/notes/2 also returns tags: [].

**Concern:**

If the endpoint treats an empty tag_names array as 'no change' and leaves the old tags in place, the note would silently retain its old tags despite the user removing them. Or if the endpoint crashes on empty tag list, the user gets an error instead of a silent failure — still wrong, but at least visible.

**Property:**

Empty tag list is valid and clears all associations

**Implies:**
- empty-tag-list-is-allowed
- tag-removal-via-put-with-empty-list
- response-with-empty-tags-array
