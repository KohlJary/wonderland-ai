## Scenario 283: Kohl opens a note that has never been saved; localStorage has a draft, server has nothing

**GUID:** 01KRY1A1CJG4S1VG4H5J0GAQBY
**Severity:** silent-wrongness

**Setup:**

Kohl created a new note (noteId is null in Editor state) and typed a title 'Experiment 42' and body 'Let me test...' into the editor. She did NOT click Save. localStorage contains {title: 'Experiment 42', body: 'Let me test...', tags: []} (no id, no revision_id, no lastSyncedAt because save never succeeded). Kohl closes the tab and reopens the app.

**Trigger:**

App boots. Editor starts with noteId=null (create mode). useEffect sees noteId is null, so it does NOT call GET /api/notes/{id}. Editor checks localStorage and finds a draft.

**Expected:**

Editor restores the draft from localStorage: title='Experiment 42', body='Let me test...', tags=[]. Kohl sees her unsaved work and can continue editing or save it. No server fetch happens because noteId is null (create mode). This is the keystroke-buffer recovery use case — unsaved drafts on new notes survive browser restart.

**Concern:**

If the editor discards the localStorage buffer for create-mode notes, Kohl loses her draft. If the editor confuses 'create-mode buffer' with 'edit-mode buffer' and tries to GET /api/notes/null, it will fail with 404 and Kohl sees an error instead of her draft.

**Property:**

unsaved_draft_recovery_on_create_mode_survives_browser_restart
