## Ticket 042: Frontend: Tag input and tag association in the editor

**GUID:** 01KRXX4GE0CW1944AM7WDJG87H
**Sources:** kohl-creates-and-saves-experimental-notes-with-markdown-bodies, kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-note-list-with-search-and-tag-filter
- Blocked by: backend-note-and-tag-crud-endpoints-with-schema
- Soft: frontend-editor-pane-with-title-markdown-body-input-and-localstorage-keystroke-buffer

**Description:**

Add tag input to editor pane. Display list of existing tags (from backend, initially empty on first load) as clickable pills or checkboxes below the body field. Allow user to type new tag name + press Enter or click 'add' to add to local state. Show selected tags as pills with delete buttons. On save (when user ships note to backend), include tag list in POST/PUT payload. Validate: tag names are non-empty, no duplicates per note. Do NOT persist tags to localStorage in this ticket — tags persist via backend only. Frontend maintains temporary tag list in component state while editing.

**Acceptance:**
- Tag input field appears in editor
- User can type tag name and press Enter to add
- Selected tags display as pills with visible delete buttons
- Deleting a pill removes tag from selection
- No duplicate tags can be added to same note
- Tag list is included in note save payload to backend

**Risk:**

If backend tag fetching is slow or tags list grows large, autocomplete complexity could add 0.5 days. Scope autocomplete to fast-follow; v1 ships with manual type-and-add only.
