## Review 030: Feature 005 blocker resolution: App.tsx navigation refactor

**GUID:** 01KRXYC1MYZT44WWZKQE8QJV1A
**Files reviewed:** src/frontend/App.tsx, src/frontend/EditorLayout.tsx
**Verdict:** request-changes

### Findings

#### block: EditorLayout receives no noteId from App state; editor always opens in create mode
**Location:** src/frontend/App.tsx:46-50
**Quote:**

```
{view === 'editor' && <EditorLayout />}
{view === 'list' && <NoteList onEdit={() => setView('editor')} />}
```

**Read:** App.tsx wires NoteList's onEdit callback to a function that only changes the view state. When Kohl clicks a note in the list, the callback receives noteId but App ignores it. EditorLayout is rendered with no props, so it has no way to know which note to load. The editor initializes in create-new mode every time.
**Concern:** Feature 005 requires Kohl to 'add tags while editing or after creation'—the 'after creation' part means clicking a note from the list and opening it for editing. This flow is broken. The noteId is calculated and passed, but dropped at the App.tsx boundary. EditorLayout cannot load the selected note because it receives no information about which note was selected.
**Request:** Refactor App.tsx to thread selectedNoteId state through to EditorLayout. (1) Add `const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null)` to App.tsx. (2) Change NoteList callback to `onEdit={(id) => { setSelectedNoteId(id); setView('editor'); }}`. (3) Pass `noteId={selectedNoteId}` to EditorLayout. (4) EditorLayout must then accept `noteId` as a prop, and on mount, if noteId is provided, fetch GET /api/notes/{noteId} to hydrate the editor with that note's data (title, body, tags). If noteId is null or undefined, EditorLayout initializes in create-new mode as it does now.

#### change-required: EditorLayout prop type mismatch: component does not accept noteId prop
**Location:** src/frontend/EditorLayout.tsx:1-20
**Quote:**

```
interface EditorLayoutProps { /* no noteId field */ }
```

**Read:** EditorLayout's props interface does not include a noteId field. The component cannot accept or use the selectedNoteId passed from App.tsx.
**Concern:** Breaking the first finding's fix (threading noteId to EditorLayout) requires EditorLayout to accept noteId as a prop. Without this interface change, App.tsx and EditorLayout are not connected.
**Request:** Add noteId?: number to EditorLayoutProps. Update EditorLayout to use this prop: on mount, if noteId is provided, call GET /api/notes/{noteId} and hydrate the form state (title, body, currentTags) from the response. If noteId is null/undefined, the editor initializes in create mode (current behavior). Store the fetched note's id and current tag list so that on save, the editor uses PATCH /api/notes/{noteId} instead of POST /api/notes.

### Approvals

- The refactoring approach is sound: thread state through React props, fetch note data on mount if an ID is provided, handle both create and edit flows conditionally. No new complexity, just wiring that was missing.
- Tweedledum correctly approved the backend. The GET /api/notes/{noteId} endpoint exists and returns the shape EditorLayout will need (id, title, body, tag_names, tag_ids, created_at, updated_at).

### Cross-domain references

- Scope ambiguity (inline tag editing in NoteList vs. edit-only in EditorLayout) is already flagged by Tweedledum's concern note. This review fixes the navigation blocking issue; the scope question should be resolved by Alice + Rabbit + Dodo before Feature 005 is marked complete.
