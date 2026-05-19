## Scenario 364: Kohl saves a note with an empty body (she types nothing); body defaults to empty string and revision_id is stable

**GUID:** 01KRY1F5JJWC63TXB9SQCCBZWK
**Severity:** silent-wrongness

**Setup:**

Kohl creates a new note with title 'Empty Body Test' and leaves the body field empty (no keystrokes, no text). She clicks Save.

**Trigger:**

The POST request body is {title: 'Empty Body Test', body: '', tag_names: []}. (The body field defaults to empty string per the backend contract.)

**Expected:**

The backend persists the note with body=''. The revision_id is computed from SHA256([title, body='', sorted_tag_ids=[], updated_at]). On subsequent loads or saves, the same note with the same empty body produces the same revision_id. If Kohl opens the note in a second tab, both tabs compute the same revision_id.

**Concern:**

If body defaults to null instead of empty string, or if the hash computation treats empty string and null differently, two tabs might compute different revision_ids even though the note state is identical. This triggers false collision warnings or allows silent overwrites.

**Property:**

empty body defaults to '' and produces consistent revision_id
