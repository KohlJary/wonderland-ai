## Review 031: Feature 005: Kohl organizes notes with optional tags — ACCEPT

**GUID:** 01KRXYDQAXYGT4WG8B582YMNQX
**Files reviewed:** frontend/src/App.tsx, frontend/src/EditorLayout.tsx, frontend/src/Editor.tsx, frontend/src/NoteList.tsx, tests/test_tag_scenarios.py
**Verdict:** accept

### Findings

#### note: Tag key generation uses stable tag_ids (correct fix from prior review)
**Location:** frontend/src/NoteList.tsx:91-96
**Quote:**

```
{note.tag_ids.map((tagId, index) => (
  <span key={`tag-${tagId}`} ...>
    {note.tag_names[index]}
  </span>
))}
```

**Read:** NoteList renders tag badges keyed by tag_id (stable) rather than array index. This is correct — React will now preserve DOM nodes if tag order changes, and no re-mounting will occur on updates.
**Concern:** None. This is the right fix.
**Request:** Implicit approval; no action needed.

#### note: Navigation contract fixed: selectedNoteId threads from NoteList → App → EditorLayout → Editor
**Location:** frontend/src/App.tsx:17-32, EditorLayout.tsx:19-26, Editor.tsx:66-92
**Quote:**

```
// App.tsx
const handleEditNote = (noteId: number) => {
  setSelectedNoteId(noteId);
  setView('editor');
};
...
{view === 'editor' && <EditorLayout noteId={selectedNoteId} ... />}

// EditorLayout
interface EditorLayoutProps {
  noteId?: number | null;
  ...
}

// Editor
if (noteId !== null && noteId !== undefined) {
  const note = await readNote(noteId);
  setState({ title: note.title, body: note.body, ... });
}
```

**Read:** The blocking navigation issue is resolved. App.tsx now threads the selected noteId through props to EditorLayout and Editor. Editor loads the note with GET /api/notes/{noteId} on mount if a noteId is provided. The feature's core use case (click note in list → open for editing) now works.
**Concern:** None. This is correct.
**Request:** Implicit approval; no action needed.

#### note: Editor correctly distinguishes create vs. update flow
**Location:** frontend/src/Editor.tsx:137-152
**Quote:**

```
if (noteId !== null && noteId !== undefined) {
  // Update existing note
  const payload: NoteUpdateRequest = {...};
  saved = await updateNote(noteId, payload);
} else {
  // Create new note
  const payload: NoteCreateRequest = {...};
  saved = await createNote(payload);
}
```

**Read:** Editor correctly routes to updateNote() when editing an existing note, and createNote() when creating a new note. The conditional is clear and the contract with the backend is respected.
**Concern:** None. This is correct.
**Request:** Implicit approval; no action needed.

#### note: NoteList renders notes in reverse chronological order with proper empty state handling
**Location:** frontend/src/NoteList.tsx:37-110
**Quote:**

```
const fetchedNotes = await listNotes();
// listNotes returns notes in reverse chronological order (per backend contract)
setNotes(fetchedNotes);
...
{!loading && notes.length === 0 && (
  <div style={styles.empty}>
    No notes yet. Start by creating your first note in the editor.
  </div>
)}
{!loading && notes.length > 0 && (
  <div style={styles.notesList}>
    {notes.map(renderNote)}
  </div>
)}
```

**Read:** NoteList fetches all notes and displays them in the order returned by the backend (reverse chronological per GET /api/notes contract). Empty state is clean and informative. Loading and error states are handled correctly.
**Concern:** None. This is correct.
**Request:** Implicit approval; no action needed.

#### note: Tag rendering skips empty tag arrays (no dead badges)
**Location:** frontend/src/NoteList.tsx:90-99
**Quote:**

```
{note.tag_names && note.tag_names.length > 0 && (
  <div style={styles.noteTags}>
    {note.tag_ids.map((tagId, index) => (
      <span key={`tag-${tagId}`} style={styles.noteTag}>
        {note.tag_names[index]}
      </span>
    ))}
  </div>
)}
```

**Read:** The conditional check ensures that notes without tags don't render an empty badge container. This is clean UX — no visual clutter for untagged notes.
**Concern:** None. This is correct.
**Request:** Implicit approval; no action needed.

#### note: Test scenarios document uncertainty about tag normalization (whitespace, case sensitivity)
**Location:** tests/test_tag_scenarios.py:5-35, 39-55
**Quote:**

```
def test_tag_names_with_whitespace_only_entries(client):
    """POST /api/notes with tag_names=['research', '  ', 'experiment'].
    
    Whitespace-only tag names should be rejected or normalized.
    Currently, '  ' (three spaces) is treated as a valid tag name.
    """
    ...
    if res.status_code == 201:
        # If accepted, the whitespace tag should be removed or normalized
        assert not any(tag.strip() == "" for tag in note["tag_names"])
    else:
        assert res.status_code == 422
```

**Read:** The test documents a specification gap: the contract does not specify whether whitespace-only tag names should be normalized (stripped), rejected, or accepted as-is. The test accepts either outcome (201 with normalization, or 422 validation error). Similar ambiguity exists for case sensitivity (are 'research', 'Research', 'RESEARCH' three tags or one?).
**Concern:** These are not implementation bugs — they are specification gaps. The team should clarify the contract before shipping Feature 005 to production. The tests document the current behavior for regression detection.
**Request:** Surface these as contract clarifications for Tweedledum and the team. See notes below.

### Approvals

- Navigation blocking issue is fully resolved. The code correctly threads selectedNoteId through App → EditorLayout → Editor, and Editor loads notes on mount if provided. Feature use case (click note to edit) now works.
- Tag key generation is fixed. Using stable tag_ids instead of array index prevents React re-mounting and is the correct pattern.
- Editor correctly distinguishes create vs. update flow, routing to createNote() or updateNote() as appropriate.
- NoteList displays notes in correct order (reverse chronological per backend contract), with proper handling of empty states, loading, and errors.
- Tag rendering skips empty tag arrays, avoiding visual clutter.
- Test scenarios comprehensively document edge cases for the team to consider (whitespace normalization, case sensitivity, concurrent creation, shared tag preservation, pagination determinism).

### Cross-domain references

- Contract clarification needed from Tweedledum (backend): tag normalization semantics. Whitespace-only tag names like '  ' (three spaces) — should these be normalized (stripped to empty, then rejected) or accepted as valid? Should leading/trailing whitespace in tag names like '  research  ' be normalized on the backend? Current implementation treats tags as case-sensitive (three separate tags for 'research', 'Research', 'RESEARCH'). Is this the intended behavior, or should tag names be normalized to lowercase for deduplication? These are not bugs; they are specification gaps in contract-note-005 (Tag Creation vs. Lookup vs. Auto-Create). Recommend: Tweedledum and the team decide on a tag normalization policy, document it in contract-note-005, and possibly add validation or sanitization to the backend endpoints.
- Scope clarification needed from Alice + Rabbit + Dodo: Feature 005 says 'Kohl adds tags to notes while editing or after creation.' Current implementation: tags can be added/edited via EditorLayout (before and after save). Tags display as read-only badges in NoteList. Is inline tag editing (add/remove tags directly in the NoteList without opening the editor) v1 scope, or is tag editing only via the EditorLayout? This doesn't block shipping the current code — Kohl can add/edit tags in the editor and see them displayed in the list. But the feature's 'after creation' semantics should be clarified before the next iteration.
