## Scenario 304: Kohl saves a note, navigates away, returns to editor, and loads the note she just saved

**GUID:** 01KRY1BD9QYCM0QJV0RZ20601C
**Severity:** breakage

**Setup:**

Kohl has just successfully saved a note (revision_id='abc...', title='Cell Biology'). She clicks 'Go to Notes List'. Then she clicks the note in the list to edit it again.

**Trigger:**

Frontend calls GET /api/notes/{id} to hydrate EditorLayout. Editor's useEffect loads the note from the response.

**Expected:**

GET /api/notes/{id} returns 200 with {id, title, body, tag_names, tag_ids, created_at, updated_at, revision_id: 'abc...'}. Editor state populates correctly. The revision_id returned matches the last saved revision_id (no silent drift). Preview renders the markdown body. Kohl sees her note exactly as she left it.

**Concern:**

If GET returns a different revision_id than the last saved one, the collision detection will fire incorrectly on the next save (Kohl gets a false collision warning). If body is corrupted or missing, Kohl loses data. If timestamps are wrong, audit trail ordering breaks.

**Property:**

Load endpoint fidelity + revision_id stability
