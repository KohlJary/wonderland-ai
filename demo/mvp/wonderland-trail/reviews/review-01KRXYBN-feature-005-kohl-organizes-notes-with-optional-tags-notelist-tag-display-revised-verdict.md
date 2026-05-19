## Review 029: Feature 005 — Kohl organizes notes with optional tags (NoteList tag display) — REVISED VERDICT

**GUID:** 01KRXYBNKZ1RBT7BFEHDYRSPMQ
**Files reviewed:** frontend/src/NoteList.tsx, frontend/src/App.tsx
**Verdict:** request-changes

### Findings

#### change-required: Tag keys use array index instead of stable tag_ids
**Location:** frontend/src/NoteList.tsx:93-99
**Quote:**

```
{note.tag_names.map((tagName, index) => (
  <span key={`${tagName}-${index}`} style={styles.noteTag}>
    {tagName}
  </span>
))}
```

**Read:** React key generation combines tag name and array index. If tag order changes on the server (reordering, tag deletion/re-add), React will re-mount DOM nodes instead of updating them.
**Concern:** Unstable keys cause unnecessary DOM re-mounts and can cause state loss in future tag-edit UI. The backend returns tag_ids (unique, stable identifiers) alongside tag_names in parallel arrays.
**Request:** Use tag_ids for keys: `key={`tag-${note.tag_ids[index]}`}`. This ensures React tracks the same tag object across re-renders even if the list is reordered.

#### suggestion: Unused onNoteClick prop clutters the interface
**Location:** frontend/src/NoteList.tsx:27-28
**Quote:**

```
interface NoteListProps {
  onNoteClick?: (noteId: number) => void;
  onEdit?: (noteId: number) => void;
}
```

**Read:** Two callback props, but App.tsx only passes onEdit. The onNoteClick handler on line 54 checks `if (onNoteClick)` but that prop is never supplied, so the branch is dead code.
**Concern:** Dead code in the interface signature creates confusion: future readers will wonder why onNoteClick exists and whether they should use it.
**Request:** Remove the onNoteClick prop and its usage (line 54 check). Keep only onEdit as the single navigation callback.

### Approvals

- Navigation from NoteList to EditorLayout now correctly threads selectedNoteId through App state — Kohl can click a note and open it for editing.
- Backend-to-frontend contract alignment is solid: GET /api/notes shape matches NoteList's field reads (id, title, body, tag_names, tag_ids, created_at).
- Empty tag list is handled gracefully — no render of empty badge row when tags are absent.
- Tag display styling is readable and visually distinct from note title/body.

### Cross-domain references

- Tag normalization (whitespace, case sensitivity) is specified in contract-note-005 but backend tests accept both normalized and raw forms — route to Tweedledum for contract clarification before v1 ships.
- Feature scope ambiguity on 'editing after creation': does this include inline tag editing in NoteList, or only via EditorLayout? Route to Alice/Rabbit for feature-scope decision.
