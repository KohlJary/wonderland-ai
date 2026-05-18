## Scenario 052: Kohl saves a note and the localStorage draft is cleared so she doesn't see stale data on her next visit

**GUID:** 01KRXTBSX1SQXPMXS4J54GRZBP
**Severity:** silent-wrongness

**Setup:**

Kohl has typed 'Rust async patterns' + 250 words into the editor. She clicks the Save button. The POST /api/notes request succeeds and returns {id: 42, title: ..., body: ..., created_at: ..., updated_at: ...}.

**Trigger:**

The Save button click triggers the POST. After the response arrives with 200 status, the editor updates to show the saved note ID and clears its internal state.

**Expected:**

The Save button becomes disabled briefly (showing loading state), then re-enables. The title and body fields remain visible (showing the saved content), OR the editor navigates to a read-only view of the note. localStorage is now empty or contains no draft (only the saved note ID, if anything). If Kohl reloads the page, she sees a blank editor (or the saved note if the app loads the note by ID from the URL).

**Concern:**

If localStorage is not cleared after save, Kohl reloads the page and sees her old draft restored alongside the saved note. She might think there are two copies, or get confused about which one is canonical. Stale drafts in localStorage break the user's mental model of 'I saved this, so it's done.'

**Property:**

successful save clears localStorage draft

**Implies:**
- user-saves-a-note-clicks-save-button-localstorage-is-cleared-so-the-draft-doesn-t-reappear
