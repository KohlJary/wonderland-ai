## Ticket 043: Frontend: Note list with search and tag filter

**GUID:** 01KRXX4GE0CW1944AM7WDJG87J
**Sources:** kohl-creates-and-saves-experimental-notes-with-markdown-bodies, kohl-can-search-notes-by-content-and-recall-via-search, kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: backend-note-and-tag-crud-endpoints-with-schema, frontend-editor-pane-with-title-markdown-body-input-and-localstorage-keystroke-buffer, frontend-tag-input-and-association-in-the-editor
- Soft: —

**Description:**

Build note list view that fetches all notes from GET /notes endpoint. Display notes as rows or cards (layout TBD in M3). Include search input field that filters notes by title or body substring (search happens client-side or via backend search endpoint, TBD in M3 contract). Include tag filter: display all tags from all notes as clickable pills; clicking a tag filters list to show only notes with that tag. Clicking a note opens it in the editor pane (or navigates to edit view, TBD). Include 'new note' button at top that clears editor and sets up new note state. Fetch notes on mount and on save (to refresh list after edit).

**Acceptance:**
- List fetches and displays all notes from backend
- Search input filters notes by title and body (case-insensitive substring match)
- Tag pills appear below search; clicking a tag filters list to show only notes with that tag
- Clicking a note opens it in editor (or navigates to edit view)
- 'New note' button clears editor state and sets up blank note for creation
- List refreshes after note is saved or deleted

**Risk:**

If search needs backend full-text indexing, scope to client-side substring match for v1 and fast-follow backend search. If tag filter becomes stateful (remembering selected tags across navigation), add 0.5 days — v1 ships with single-tag filter only.
