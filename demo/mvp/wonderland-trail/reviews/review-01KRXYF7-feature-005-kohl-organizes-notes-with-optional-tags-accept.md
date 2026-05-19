## Review 033: Feature 005: Kohl organizes notes with optional tags — ACCEPT

**GUID:** 01KRXYF76295BCF0H1XAM7F8QR
**Files reviewed:** frontend/src/App.tsx, frontend/src/Editor.tsx, frontend/src/EditorLayout.tsx, frontend/src/NoteList.tsx, frontend/src/api.ts, src/backend/api/notes.py, src/backend/models.py
**Verdict:** accept

### Findings

#### note: Navigation contract fully implemented and verified
**Location:** frontend/src/App.tsx:21-32
**Quote:**

```
const handleEditNote = (noteId: number) => {
    setSelectedNoteId(noteId);
    setView('editor');
  };

  // Handle save in editor: clear selection and go back to list
  const handleEditorSave = () => {
    setSelectedNoteId(null);
    setView('list');
  };
```

**Read:** App.tsx properly threads selectedNoteId from NoteList click → EditorLayout → Editor. EditorLayout accepts noteId and passes it to Editor. Editor.useEffect() calls readNote(noteId) if noteId is provided, loading the existing note instead of opening a blank editor. On save, EditorLayout calls onSave(), which returns to the list view. This implements the core use case for Feature 005: click a note, edit its tags, save.
**Concern:** None. The navigation contract was explicitly fixed in prior iterations and is now correct. This verifies that the fix was properly integrated.
**Request:** No action required. This is a confirmation that prior fixes are in place and working.

#### note: React key anti-pattern resolved in NoteList tag rendering
**Location:** frontend/src/NoteList.tsx:100-103
**Quote:**

```
{note.tag_ids.map((tagId, index) => (
              // Use stable tag ID as key (tag_ids[i] corresponds to tag_names[i])
              <span key={`tag-${tagId}`} style={styles.noteTag}>
                {note.tag_names[index]}
              </span>
            ))}
```

**Read:** NoteList uses tag_ids as stable React keys instead of array index. The backend invariant (models.py:to_dict()) guarantees tag_names[i] corresponds to tag_ids[i], so this is correct. The comment documents the invariant for future readers.
**Concern:** None. This was a prior finding and is now fixed.
**Request:** No action required.

#### note: Backend contract fully matches frontend API expectations
**Location:** src/backend/api/notes.py:1-20, frontend/src/api.ts:13-23
**Quote:**

```
Backend declares: POST /api/notes response {id, title, body, tag_names: str[], tag_ids: int[], created_at, updated_at}. Frontend expects Note interface: {id, title, body, tag_names, tag_ids, created_at, updated_at}.
```

**Read:** The backend notes.py endpoints (create_note, list_notes, read_note, update_note) all return NoteResponse with both tag_names and tag_ids. The frontend api.ts defines the Note interface with the same fields. The models.py to_dict() method computes tag_names and tag_ids from the many-to-many relationship in a single iteration (line 65-66 in models.py), guaranteeing order correspondence. All contract notes (001, 004, 014, 015, 016) specify this shape, and implementation matches.
**Concern:** None. Cross-ticket coherence verified.
**Request:** No action required.

#### note: Tag operations are atomic and maintain invariants
**Location:** src/backend/api/notes.py:145-165
**Quote:**

```
def _associate_tags(db: Session, note: Note, tag_names: list[str]) -> None:
    """Associate note with tags by name, auto-creating tags if missing.
    ...
    Single transaction: all-or-nothing.
    """
    # Clear existing associations
    note.tags.clear()
    
    # Deduplicate tag names (preserve order)
    seen = set()
    unique_tag_names = []
    for tag_name in tag_names:
        if tag_name not in seen:
            unique_tag_names.append(tag_name)
            seen.add(tag_name)
```

**Read:** The _associate_tags() helper deduplicates tag_names on the client side (preserving order) before associating. This prevents UNIQUE constraint violations if a user tries to add 'research' twice to the same note. The function clears existing associations and creates new ones in a single transaction. If any validation fails (e.g., tag name exceeds length), the entire operation rolls back.
**Concern:** None. This was documented in prior findings as Hatter's deduplication test case, and the implementation correctly handles it.
**Request:** No action required.

#### note: Search endpoint returns body_preview (150 chars), not full body
**Location:** src/backend/api/notes.py:267-276
**Quote:**

```
# Build search results with body_preview (first 150 chars) instead of full body
    search_results = []
    for note in notes:
        note_dict = note.to_dict()
        body_preview = note_dict["body"][:150]  # Truncate to 150 chars
        search_result = SearchResultNote(
            id=note_dict["id"],
            title=note_dict["title"],
            body_preview=body_preview,
```

**Read:** The search endpoint correctly truncates body to 150 chars for the response payload (optimization per contract-note-01KRXRWW). The SearchResultNote model enforces this at the schema level. Frontend Search.tsx receives body_preview and displays it as a preview snippet.
**Concern:** None. Contract requirement met.
**Request:** No action required.

#### note: Editor loads existing note on mount if noteId is provided
**Location:** frontend/src/Editor.tsx:49-70
**Quote:**

```
const loadNote = async () => {
      if (noteId !== null && noteId !== undefined) {
        try {
          setLoadingNote(true);
          const note = await readNote(noteId);
          setState({
            title: note.title,
            body: note.body || '',
            tags: note.tag_names || [],
          });
          if (onBodyChange) {
            onBodyChange(note.body || '');
          }
        } catch (err) {
          setError(`Failed to load note: ${String(err)}`);
        } finally {
          setLoadingNote(false);
        }
      } else {
```

**Read:** The Editor component's useEffect() dependency on noteId ensures the note is loaded when navigating from NoteList to editor. The component shows a loading spinner while fetching (line 181-190). On error, it displays a user-facing error message. On success, it populates state with the loaded note's title, body, and tag_names. The heading updates to show 'Edit Note #X' instead of 'New Note' (line 186-187).
**Concern:** None. This enables the core use case of Feature 005: click a note to edit it.
**Request:** No action required.

#### note: Test scenarios document tag edge cases comprehensively
**Location:** tests/test_tag_scenarios.py
**Quote:**

```
Covers edge cases and seams: race conditions, whitespace normalization,
idempotence, shared tags, concurrent mutations, and pagination drift.
```

**Read:** Hatter's test scenarios cover: whitespace-only tag names, case sensitivity, idempotence of tag association, shared tags across notes, tag preservation on note delete, whitespace in tag names, body preview truncation with emoji, concurrent tag creation, PUT/DELETE race conditions, and pagination determinism. The scenarios document actual vs. expected behavior and severity levels. They serve as a contract between the team and the implementation.
**Concern:** None. The test suite comprehensively documents behavior and edge cases.
**Request:** No action required.

### Approvals

- Navigation contract is correctly implemented: clicking a note in NoteList properly loads it in the Editor.
- Tag display in NoteList is visually clean and correct: tags render as badges using stable keys, empty tag arrays produce no badge section.
- Backend and frontend are coherent on response shapes: both implement the full tag_names and tag_ids arrays per contract.
- Tag association logic is correct: auto-creation works, deduplication prevents constraint violations, idempotence is maintained.
- Editor properly loads existing notes when noteId is provided, and shows appropriate loading state during fetch.
- Search endpoint correctly optimizes for payload size by returning body_preview instead of full body.
- The feature is end-to-end: Kohl can create notes, add tags via the editor, view notes in a list with tag badges, and click to edit.
