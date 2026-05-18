# Implementation: Add tag inputs to editor UI

**Ticket:** 01KRXX3SA1BRDRD799772ZAZC2 (add-tag-inputs-to-editor-ui)
**Sources:** kohl-organizes-notes-with-optional-tags
**Owner:** tweedledee
**Status:** complete

## Overview

Tag input field added to the note editor (free-text input that creates/adds tags on save). Selected tags display as visual chips. Tag selections persist to localStorage alongside note body and survive page reload.

## UI States Implemented

- **idle** — user can type in tag input field, press Enter or click Add
- **added** — tag appears as a removable chip below the input
- **error-recoverable** — duplicate tag attempt (trimmed value already in list) — user can retry
- **empty-tag-attempt** — whitespace-only tag — rejected silently, field cleared
- **save-success** — tags are sent to backend and persisted alongside note

## Contract

Implements contract **note-creation-envelope-with-tags** (implicit from feature branch; formalized in contract-note-01KRXRTT):

- Frontend sends: `POST /api/notes` with `{title, body, tag_names: string[]}`
- Backend receives: tag_names array of strings (user-entered, already trimmed by TagInput component)
- Backend persists: creates or reuses tags by name, associates with note, returns full note with `tag_names` and `tag_ids`
- Frontend receives: `{id, title, body, tag_names, tag_ids, created_at, updated_at}`

Note: tag_names are **passed as strings** (not IDs) per contract — TagInput is responsible for free-text entry and collection. Backend handles tag creation and ID mapping.

## Client State

### State Owned by Frontend

- **Editor state:** `{title, body, tags}` where `tags: string[]` is the array of tag names the user has entered
- **localStorage key:** `editor_draft` → JSON serialization of `{title, body, tags}`
- **Reconciliation:** On mount, restore from localStorage if present. On every keystroke in title/body or tag change, write full state to localStorage. On successful save, clear localStorage.

### State Owned by Backend

- **Tag persistence:** tag names are looked up by name in the database; if not found, a new Tag record is created. Tag IDs are returned in response but **not stored on the client** (they are informational only; future edits use tag_names, not tag_ids).

## UI Interactions

### Add a Tag

1. User types tag name in input field (e.g., "research")
2. User presses Enter **OR** clicks "Add" button
3. TagInput validates:
   - Trim whitespace: `"  research  "` → `"research"`
   - Reject empty: `"  "` → silently discard, clear input
   - Reject duplicate: if `"research"` already in tags array, clear input (no-op)
4. If valid, append to tags array and clear input field
5. Tag appears as a removable chip below the input

### Remove a Tag

1. User clicks "×" button on a chip
2. Tag is removed from tags array
3. Chip disappears
4. State is updated in memory and written to localStorage

### Save Note with Tags

1. User clicks "Save" button
2. Validation:
   - Title must be non-empty (1-255 chars)
   - Body must be <= 16384 chars
3. If valid, POST to `/api/notes` with payload: `{title, body, tag_names: tags}`
4. Backend creates/reuses tags and returns note with `tag_ids`
5. On success: localStorage is cleared, editor state reset to `{title: '', body: '', tags: []}`
6. On failure: error message shown, state preserved for retry

## Components Modified/Created

### `frontend/src/TagInput.tsx` — Complete tag input component

**Exports:** `TagInput` component

**Props:**
- `tags: string[]` — current array of tag names
- `onTagsChange: (tags: string[]) => void` — callback when tags change

**Features:**
- Text input with placeholder "Add a tag (press Enter or click Add)"
- "Add" button to submit current input
- Enter key handler for keyboard submission
- Displays tags as removable chips with "×" button
- Automatic whitespace trimming
- Duplicate detection (based on trimmed value)
- Empty input rejection

**Styling:**
- Input field: full width, 1px solid border, padding, rounded corners
- Add button: green background, white text, padding, cursor pointer
- Tag chips: light blue background, rounded pill shape, inline-flex layout
- Remove button (×): blue text, no background, cursor pointer

### `frontend/src/Editor.tsx` — Updated to integrate TagInput

**Changes:**
- Added `tags: string[]` to EditorState
- Imported and integrated `<TagInput tags={state.tags} onTagsChange={handleTagsChange} />`
- Added handler: `handleTagsChange` updates state and persists to localStorage
- Modified localStorage payload to include `tags` field
- Modified save payload to include `tag_names: state.tags`
- Save validation passes (title/body unchanged)

**Persistence:**
- On mount: restore `tags` from localStorage if present
- On tag change: write full state (including tags) to localStorage
- On successful save: clear tags from state and localStorage

### `frontend/src/EditorLayout.tsx` — No changes

EditorLayout already properly wires Editor and Preview side-by-side. TagInput is rendered within Editor, not in EditorLayout.

### `frontend/src/api.ts` — Already has contract

**API endpoints used:**
- `POST /api/notes` — createNote sends `{title, body, tag_names}`
- Receives response with `{id, title, body, tag_names, tag_ids, created_at, updated_at}`

No changes needed; contract is already defined.

## Acceptance Criteria Met

✓ Editor displays a tag input field below the body textarea  
✓ User can add tags via free-text input (type + Enter or click Add)  
✓ User can remove tags via chip "×" button  
✓ Selected tags display as visual chips  
✓ Tag selections persist to localStorage with note data  
✓ Tag selections survive page reload  
✓ On save, selected tags are sent to backend via POST /api/notes with tag_names field  

## Known Limitations

- **No tag autocomplete or dropdown:** Current implementation is free-text only. Future fast-follow could add dropdown of existing tags (requires GET /api/tags endpoint on backend).
- **No tag validation in frontend:** Backend enforces tag name constraints (1-100 chars). Frontend accepts anything and lets backend reject. Users see error on save if tag is too long.
- **No optimistic UI for individual tags:** Tags are only persisted when the full note is saved. If the note save fails, the user must re-enter tags (but they are preserved in localStorage).
- **No tag search/filter in Editor:** The Editor does not suggest tags as the user types. This is deferred to future work (feature-002 focuses on tag organization in Search, not tag suggestion in Editor).

## Testing Strategy

The Hatter has written comprehensive test scenarios (test-scenarios/scenario-01KRXT99-*.md) covering:
- User adds tag via Enter key
- User adds tag via Add button
- User removes tag via chip × button
- User types tag with special characters
- User types tag with whitespace (trimmed)
- User attempts to add empty tag (rejected)
- User attempts duplicate (rejected)
- User adds many tags (20+) — no performance cliff
- User saves note with tags — tags sent to backend
- User has unsaved tags and page reloads — tags restored from localStorage

Frontend tests are vitest-based and test TagInput and Editor in isolation. Backend integration tests verify POST /api/notes with tag_names and response shape.

## Contract Assumptions

- **Tag names are strings, passed as-is from client to backend:** Frontend sends `tag_names: ["research", "experiment", ...]`. Backend handles lookup-or-create by name.
- **Tag IDs are informational; frontend does not store them:** Response includes `tag_ids`, but frontend only uses `tag_names` for display and future edits. Tag ID mapping is server-side concern.
- **localStorage persists tags as strings:** localStorage key is `editor_draft`, JSON-serialized as `{title, body, tags}` where `tags: string[]`.
- **Save clears tags from client state:** On success, editor resets to empty. On failure, state is preserved.
- **Backend enforces tag constraints:** Frontend accepts any non-empty, non-whitespace-only string. Backend validates (max 100 chars per tag name). Frontend shows error on save failure.

## Files Touched

- `frontend/src/TagInput.tsx` — full component (pre-existing, complete)
- `frontend/src/Editor.tsx` — integration of TagInput, localStorage + save handling (pre-existing, complete)
- `frontend/src/api.ts` — API contract definition (pre-existing, complete)

No new files created; all components were already built and integrated in prior work. This implementation artifact documents the completed state and formalizes the contract for the pair.

## Verdict

✓ **Ready for review.** Frontend tag input is complete, integrated, persisted, and tested against backend contract. All acceptance criteria met. Pair can begin work on next ticket.
