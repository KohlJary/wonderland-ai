## Review 028: Feature 005: Kohl organizes notes with optional tags

**GUID:** 01KRXYAFFDVQX0K46CAAGYH1DB
**Files reviewed:** frontend/src/App.tsx, frontend/src/NoteList.tsx, src/backend/api/notes.py, frontend/src/EditorLayout.tsx
**Verdict:** block

### Findings

#### block: NoteList-to-Editor navigation is broken: selected note ID never reaches EditorLayout
**Location:** frontend/src/App.tsx:46, frontend/src/NoteList.tsx:53-60
**Quote:**

```
// App.tsx
{view === 'list' && <NoteList onEdit={() => setView('editor')} />}
{view === 'editor' && <EditorLayout />}

// NoteList.tsx
const handleNoteClick = (noteId: number) => {
  if (onEdit) {
    onEdit(noteId);
  }
};
```

**Read:** When a user clicks a note in NoteList, handleNoteClick fires and calls onEdit(noteId). The App passes `onEdit={() => setView('editor')}`, a callback that ignores the noteId argument entirely. EditorLayout has no mechanism to receive or load a specific note ID — it will always start in create-new-note mode, never edit mode.
**Concern:** The feature claim is 'Kohl adds tags to notes while editing or after creation, and can browse notes grouped by tag.' The browsing works (NoteList displays notes), but clicking a note to edit it fails silently — the user gets a blank editor instead of the selected note's content. This is a critical UX break and a blocker for the feature.
**Request:** Refactor the view state to track the selected note ID. Pass it to EditorLayout so it can load the right note on mount. Approach: `const [view, setView] = useState<'editor' | 'search' | 'list'>('editor'); const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);` then `onEdit={(id) => { setSelectedNoteId(id); setView('editor'); }}` and `{view === 'editor' && <EditorLayout noteId={selectedNoteId} />}`. EditorLayout would need to accept an optional `noteId` prop and load that note on mount if provided.

#### change-required: Tag key generation uses array index instead of stable tag ID
**Location:** frontend/src/NoteList.tsx:99
**Quote:**

```
<span key={`${tagName}-${index}`} style={styles.noteTag}>
  {tagName}
</span>
```

**Read:** The code generates a key from the tag name and array index. If tags are reordered or added/removed from the middle of the list, React will re-mount DOM nodes instead of updating them in place.
**Concern:** Using index as part of a key is an anti-pattern in React. If a note's tags are updated (e.g., user removes 'research' from the middle of a 3-tag list), the remaining tags will be re-keyed and their DOM nodes will be torn down and recreated. More importantly, the code has access to `tag_ids`, which are stable identifiers — using them would be correct.
**Request:** Use `tag_ids` instead of array index for the key. Modify to: `key={`tag-${note.tag_ids[index]}`}`. If tag_ids and tag_names are not guaranteed to be in the same order, refactor to iterate over tag_ids with a lookup into tag_names.

#### change-required: Callback prop signature mismatch: onEdit prop promises noteId but caller ignores it
**Location:** frontend/src/NoteList.tsx:28, frontend/src/App.tsx:46
**Quote:**

```
interface NoteListProps {
  onEdit?: (noteId: number) => void;
}

// App.tsx passes:
onEdit={() => setView('editor')}
```

**Read:** NoteList defines onEdit as `(noteId: number) => void`, implying the caller will receive the selected note's ID. However, App.tsx passes a callback that ignores the argument.
**Concern:** This is a contract violation. The prop's type promise is broken. The next developer reading this interface will assume they can use the noteId argument, but they won't receive it. This is misleading and wastes debugging time.
**Request:** Remove the `noteId` parameter from the onEdit prop type, or fix the calling site in App.tsx to actually use it. If you're refactoring for the first finding (threading noteId through), use that solution. Otherwise, simplify the prop to `onEdit?: () => void`.

#### suggestion: Dead code: onNoteClick prop is defined but never used
**Location:** frontend/src/NoteList.tsx:28, 53-60
**Quote:**

```
interface NoteListProps {
  onNoteClick?: (noteId: number) => void;
  onEdit?: (noteId: number) => void;
}

const handleNoteClick = (noteId: number) => {
  if (onNoteClick) {
    onNoteClick(noteId);
  } else if (onEdit) {
    onEdit(noteId);
  }
};
```

**Read:** The NoteListProps interface defines onNoteClick, and handleNoteClick checks for it before falling back to onEdit. But App.tsx never provides onNoteClick, so the check always falls through to onEdit. The prop exists in the interface but is never actually called.
**Concern:** Dead code increases surface area for confusion. A future maintainer reading this interface might assume onNoteClick is the primary way to handle clicks and spend time debugging why it's never invoked.
**Request:** Remove the onNoteClick prop from NoteListProps and simplify handleNoteClick to just call onEdit directly. If there's a legitimate future use case for onNoteClick (e.g., multi-select mode), document it in a comment or file a separate story, rather than shipping it unused.

#### note: Contract coherence: backend and frontend agree on response shape and field usage
**Location:** frontend/src/api.ts:10-13, src/backend/api/notes.py:1-10, frontend/src/NoteList.tsx:4-8
**Quote:**

```
// Contract specified
// GET /api/notes: {id, title, body, tag_names: string[], tag_ids: number[], created_at, updated_at}

// Backend (api/notes.py docstring)
// GET /api/notes: response 200 [{id, title, body, tag_names, tag_ids, created_at, updated_at}]

// Frontend (NoteList.tsx comment)
// - GET /api/notes: → Note[] (reverse chronological, includes tag_names and tag_ids)
```

**Read:** The contract notes (01KRXRVT, 01KRXXDG) specify that GET /api/notes returns both tag_names and tag_ids. The backend implementation includes both fields in NoteResponse. The frontend api.ts defines the Note interface with both fields. NoteList.tsx correctly reads and displays tag_names, leaving tag_ids available for future use.
**Concern:** None — contract alignment is verified across all three layers.
**Request:** None. This is affirming correct work.

### Approvals

- Contract coherence verified: backend response shape matches frontend interface definitions. No field name mismatches or missing fields.
- Reverse chronological ordering is correct: backend returns notes sorted by updated_at DESC, id DESC; frontend displays in received order without re-sorting.
- Empty tags case is handled correctly: the conditional check avoids rendering empty badge sections.
- Tag badge styling is visually distinct and well-designed: light blue background, rounded corners, text truncated with whitespace-nowrap to prevent wrapping.
- Accessibility is present: note items are keyboard-navigable (role='button', tabIndex, onKeyDown handlers for Enter and Space).
- Error state is handled: component displays error message and Retry button if note fetch fails.

### Cross-domain references

- Frontend navigation refactoring (first finding) may affect Editor component contract — Editor should accept optional noteId prop and implement load-on-mount logic
- This feature realizes the 'read' side of tag functionality; the 'write' side (TagInput in Editor) was already reviewed in Feature 005-backend-and-frontend-tagging implementation
