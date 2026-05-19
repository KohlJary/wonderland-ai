## Scenario 007: Kohl saves a note with an empty body — the schema allows optional body content

**GUID:** 01KRXSC2B76HKK0C1NK7MRJY5W
**Severity:** silent-wrongness

**Setup:**

Kohl opens the editor and enters only a title: 'Observation 2024-01-15'. She does not enter any body text (the markdown editor is empty). She clicks Save.

**Trigger:**

The editor sends POST /api/notes with {title: 'Observation 2024-01-15', body: '', tag_names: []}. The backend receives the request and attempts to insert the note into the schema.

**Expected:**

The backend returns 200 and the note is persisted. Kohl can see the note in the list (title visible) and can open it in the editor (title displays, body is empty or blank). The schema permits empty body because research notes sometimes start with just a title and are expanded later.

**Concern:**

If the schema enforces body as NOT NULL, the save fails with a 400 validation error. Kohl sees 'Save failed: body is required' but she did not intend to fill the body. This is a silent wrongness because the system rejects a valid user action without clear feedback. Alternatively, if the schema accepts empty body but the frontend doesn't expect it (e.g., undefined instead of empty string), the UI might display 'body is undefined' or crash — that's also silent wrongness (appears to work but displays garbage).

**Property:**

The schema allows a note with a non-empty title and optional or empty body.

**Implies:**
- Note.body is nullable or has a default empty string
- Insertion with body='' or body=NULL succeeds and returns 200
- Retrieval of that note returns body as empty string (not NULL, not undefined, for frontend predictability)
