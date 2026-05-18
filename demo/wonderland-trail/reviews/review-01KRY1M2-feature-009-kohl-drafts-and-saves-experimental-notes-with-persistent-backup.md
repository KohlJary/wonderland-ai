## Review 046: Feature 009: Kohl drafts and saves experimental notes with persistent backup

**GUID:** 01KRY1M2WR7JSYEZSZX1ZV7JPM
**Files reviewed:** frontend/src/App.tsx, frontend/src/Editor.tsx, frontend/src/NoteList.tsx, frontend/src/TagInput.tsx, frontend/src/api.ts, frontend/src/useBootNotes.ts, frontend/src/useLocalStorageDebounce.ts, src/backend/api/notes.py, src/backend/models.py
**Verdict:** request-changes

### Findings

#### change-required: useBootNotes merging logic incomplete vs. contract description
**Location:** frontend/src/useBootNotes.ts:51-65
**Quote:**

```
// For now, no merging logic per the optimistic strategy:
        // - If backend notes exist, use them as the source of truth for the list view
        // - Editor component handles its own localStorage restoration via noteId prop
        // - The keystroke buffer for new notes (noteId = null) is handled by Editor's own useEffect
```

**Read:** The hook's JSDoc promises a merge strategy where 'localStorage keystroke buffer takes precedence if present,' but the implementation only fetches backend notes and returns them. The LocalStorageBuffer interface is defined but never used.
**Concern:** The function's contract (in its JSDoc) and implementation diverge. Callers reading the JSDoc will expect merge logic that doesn't exist. This creates two problems: (1) future readers of the code will be confused about what the function actually does, and (2) if Kohl uses two tabs and has a keystroke buffer in one while the other is loading, the buffer will be silently discarded.
**Request:** Either: (A) implement the merge logic described (iterate backend notes, check localStorage buffers per note, apply merge strategy), or (B) simplify the JSDoc to match the implementation ('loads persisted notes from backend; per-note buffers handled by Editor component'). Choose B if the merge responsibility truly belongs in Editor; choose A if this hook owns the responsibility. The current state is halfway between, which is the worst place to be.

#### change-required: Editor state initialization creates implicit contract with revision_id
**Location:** frontend/src/Editor.tsx:52
**Quote:**

```
const [state, setState] = useState<EditorState>({ title: '', body: '', tags: [], revision_id: null });
```

**Read:** EditorState is initialized with revision_id: null. This is correct for new unsaved notes. But the comment in EditorState interface says 'null for new notes; cached for collision detection,' which is accurate but incomplete — what happens if the editor loads an existing note from localStorage that was saved but then the tab was closed? The revision_id from localStorage may be stale.
**Concern:** The Editor component has three sources of truth: (1) backend loaded via readNote (has current revision_id), (2) localStorage keystroke buffer (may have stale revision_id), (3) server state loaded on conflict (has current revision_id). When the Editor chooses 'keep_buffer' in a conflict, it sets revision_id to null. This is correct because the buffer may have been edited since the last successful save, so its old revision_id is not valid. But if a keystroke buffer is restored on mount without conflict, its cached revision_id is used, which could be stale if the note was edited elsewhere (e.g., on another device). The code handles the case where server is newer (it discards the buffer), but doesn't handle the case where the buffer's revision_id is simply outdated because the note was edited in another session on the same device.
**Request:** Add a comment clarifying the revision_id invariant in EditorState: 'revision_id is null for new notes and for buffers whose revision_id is unknown or stale (e.g., restored from localStorage). On successful save, revision_id is set to the server response. On conflict, revision_id is set to null because the buffer is in an uncommitted edit state.' This is defensive documentation that will protect future readers (and you in three months) from the temptation to trust a stale revision_id from localStorage.

#### suggestion: conflictState vs. conflict naming creates subtle reader confusion
**Location:** frontend/src/Editor.tsx:49, 61-62, 176-213, 339-395
**Quote:**

```
interface ConflictState {
  serverVersion: Note;
  bufferVersion: EditorState & { lastModified: number };
}
...
const [conflict, setConflict] = useState<ConflictState | null>(null);
const [conflictState, setConflictState] = useState<ConflictState | null>(null);
```

**Read:** There are two state variables holding the same type: `conflict` and `conflictState`. The `conflict` is used for boot-time conflicts (when the Editor loads an existing note and finds a newer keystroke buffer), while `conflictState` is used for save-time conflicts (409 from the backend). Both show a conflict UI to the user, but the variable names don't distinguish the scenario.
**Concern:** A reader scanning the code will see two variables of the same type in the same component and will have to trace each one to understand the difference. The names suggest synonymy, not distinct scenarios. This is not a bug — the logic is correct — but it's a clarity bug. Future readers will waste time understanding why there are two. If the code needs modification (e.g., to unify the conflict UI), the distinction will not be immediately obvious.
**Request:** Rename for clarity. Consider: `bootConflict` and `saveConflict`, or `conflict` and `collisionOnSave`, or some other pair that makes the distinction obvious at the point of declaration. The rule: if two variables of the same type exist in the same scope, their names should immediately explain why there are two.

#### suggestion: Debounce delay hard-coded in Editor; inconsistent with constant definition
**Location:** frontend/src/Editor.tsx:62
**Quote:**

```
const debouncedSaveToStorage = useLocalStorageDebounce<EditorState>(LOCALSTORAGE_KEY, 2000);
```

**Read:** The debounce delay is hard-coded as 2000ms (2 seconds). The file does not define a constant for this value, so the magic number appears once in the code.
**Concern:** Magic numbers reduce clarity. If the team's spec or design doc says '2 seconds per ticket-068,' the magic number should be named to link back to that requirement. Even a comment would help — '// Per ticket-068: keystroke buffer batching' — so a future reader knows where the number came from.
**Request:** Add a named constant: `const KEYSTROKE_DEBOUNCE_MS = 2000; // Per ticket-068: buffer debouncing to reduce localStorage writes` and use it in the useLocalStorageDebounce call. This makes the intent explicit and makes it searchable.

#### suggestion: TagInput disabled prop not wired in Editor's error state
**Location:** frontend/src/Editor.tsx:470
**Quote:**

```
<TagInput tags={state.tags} onTagsChange={handleTagsChange} disabled={loading || conflictState !== null} />
```

**Read:** TagInput is disabled when loading or conflictState is not null. This is correct for the conflict modal. However, the component is not disabled when there is a boot-time conflict (the `conflict` variable is not null), even though the conflict modal for boot-time conflicts also disables the input.
**Concern:** Inconsistency. When showing the boot-time conflict merge UI, the entire Editor returns early and renders a different UI (the merge UI at line 339), so TagInput is not even rendered. But the pattern is not consistent — the boot-time conflict uses early return, while the save-time conflict uses a modal overlay. If the code is refactored to show both conflicts as modals, the disabled prop would need to be updated.
**Request:** No change required for this review, but note this for future refactoring: the two conflict scenarios (boot-time and save-time) use different UI patterns (early return vs. modal). If they're ever unified, the disabled state consistency will need to be verified. Not a bug, but a potential future trap.

#### note: Collision detection spec vs. test scenario alignment not verified
**Location:** frontend/src/Editor.tsx:80-103
**Quote:**

```
if (bufferTime > serverTime) {
                // Buffer is newer: show merge UI (per test scenario 253)
                setConflict({
                  serverVersion: serverNote,
                  bufferVersion: {
                    ...bufferData,
                    lastModified: bufferTime,
                  },
                });
                setLoadingNote(false);
                return;
              } else if (bufferTime === serverTime) {
                // Same timestamp: buffer matches server, discard buffer (per test scenario 255)
                localStorage.removeItem(LOCALSTORAGE_KEY);
                localStorage.removeItem(LOCALSTORAGE_TIMESTAMP_KEY);
              }
```

**Read:** The code references test scenarios 253 and 255 by number. These are presumably scenarios from Mad Hatter's test_scenarios artifact, but they're not present in the context provided for this review.
**Concern:** I cannot verify that the implementation matches the test scenarios it claims to implement. The code says 'if buffer is newer, show merge UI (per test scenario 253),' but without seeing scenario 253, I cannot confirm the implementation is correct. This is a cross-domain reference that should be resolvable but isn't in my current context.
**Request:** No code change needed. This is a note for the Mad Hatter: verify that test scenarios 253 and 255 (and any others referenced in the code) are actually defined, and that their assertions match the Editor's behavior. The code references are good practice; just make sure the scenarios exist.

#### change-required: Backend 409 response structure in frontend doesn't handle parsed error response correctly
**Location:** frontend/src/Editor.tsx:306-318
**Quote:**

```
saved = await updateNote(noteId, payload, state.revision_id || undefined);
        
        // Handle 409 Conflict response
        if (saved && 'conflict' in saved) {
          const conflict = saved.conflict;
          // Show collision UI with server's current state
          setConflictState({
            serverVersion: conflict.server_state,
            bufferVersion: {
              title: state.title,
              body: state.body,
              tags: state.tags,
              revision_id: state.revision_id,
              lastModified: Date.now(),
            },
          });
```

**Read:** The Editor expects updateNote to return an object with shape `{ conflict: ConflictError }` on 409. The api.ts file (lines 102-107) does catch 409 and return `{ conflict: conflictData }`, so the contract matches. But the structure of `conflictData` is not type-checked — it's just the raw JSON response.
**Concern:** The code assumes the 409 response has the shape `{ error, server_revision_id, server_state }` (per the ConflictError interface in api.ts), but the backend returns `{ error, message, server_revision_id, server_state }` (see src/backend/api/notes.py:389-395). The extra `message` field is harmless, but the code should be explicit about what structure it expects. If the backend response changes, the code will silently use wrong data.
**Request:** Make the conflict error response structure explicit. In api.ts, define the expected response shape as a type and parse it before returning. Example: `type ConflictResponse = { error: string; message: string; server_revision_id: string; server_state: Note }; const conflictData: ConflictResponse = await res.json(); return { conflict: conflictData };`. This ensures the response is validated at the API boundary, not in the component.

#### change-required: Backend: revision_id computation happens on every GET, creating redundant hashing
**Location:** src/backend/api/notes.py:372-378, 413-430
**Quote:**

```
# Compute current revision_id before any updates
    tag_ids_before = [tag.id for tag in note.tags]
    current_revision_id = compute_revision_id(note.title, note.body, tag_ids_before, note.updated_at.isoformat())
```

**Read:** Every GET endpoint (list_notes, read_note, search_notes, and also on every PUT) computes revision_id by hashing the note state. This is correct for deterministic collision detection, but it's also expensive — each request recalculates the same hash.
**Concern:** This is a performance issue in a read-heavy system. If there are 100 notes and Kohl loads the notes list, the server computes 100 SHA256 hashes. If she then opens a note in the editor, that's another hash computation. Most production systems would cache the revision_id in the database so it can be returned without recomputation. However, for the MVP scope (single-user, small dataset), this is acceptable performance-wise. The real concern is maintainability: if revision_id ever needs to change (e.g., to include additional state in the hash), every endpoint needs to be updated. The code duplication (compute_revision_id calls spread across multiple endpoints) makes this fragile.
**Request:** Consider caching revision_id as a database column (computed on every write, cached on reads). For now, this is acceptable, but document it. Add a comment on compute_revision_id(): '// TODO: cache in database to avoid recomputation on every GET. For MVP, recomputation is acceptable; revisit after performance testing.' This flags the tradeoff for future readers.

#### note: Audit trail implemented but telemetry not wired to observability
**Location:** src/backend/api/notes.py:38-99
**Quote:**

```
def _record_audit_log(
    db: Session, 
    note_id: int, 
    title: str, 
    body: str, 
    tag_ids: list[int], 
    updated_at: str,
    collision_detected: bool = False,
    conflicting_revision_id: str | None = None
) -> str:
```

**Read:** The backend creates audit_log entries for every save (success or collision) with full-state snapshots, timestamps, and collision detection flags. This is excellent forensic completeness. But there's no log or observability signal — the audit trail is written to the database but not exposed as structured logs or metrics.
**Concern:** The Dormouse (observability agent) will not see save patterns, collision rates, or user activity unless there's a log message or metric. The audit trail is forensic-complete for post-mortem analysis, but it doesn't feed into real-time observability. For the MVP, this is acceptable — the team will need to query the audit_log table directly to understand behavior.
**Request:** No code change required for this review. This is a cross-domain note for the Dormouse: the audit trail table is populated with every save, but there are no structured logs or metrics being emitted. Consider adding a log line at save time (success and collision) so the Dormouse can instrument production behavior. Example: `logging.info('note_save', extra={'note_id': note.id, 'collision_detected': False, 'revision_id': revision_id})` at save time.

#### suggestion: NoteList component now has no local data-fetching logic; dependency on parent is not documented
**Location:** frontend/src/NoteList.tsx:24-29
**Quote:**

```
export function NoteList({ notes, onEdit, syncStatus = 'idle', syncError = null }: NoteListProps) {
  // Per ticket-066: loading state is managed by App's useBootNotes hook
  // NoteList receives notes directly, no local fetching
  const loading = syncStatus === 'syncing';
  const error = syncStatus === 'error' ? syncError : null;
```

**Read:** NoteList was previously a self-contained component that fetched its own data. Now it's a pure data-presentation component that receives notes from its parent (App) via props, along with sync status. The comment explains the change.
**Concern:** The comment is helpful, but the component is now fragile — if someone tries to use NoteList in a different context without providing the `notes` prop, it will render an empty list. There's no clear contract about what the parent (App) is responsible for. The comment should be more explicit about the responsibility boundary.
**Request:** Enhance the JSDoc for NoteList to make the contract explicit: '// NoteList is a pure presentation component — it does not fetch data. The parent (App) is responsible for fetching via useBootNotes and passing notes + syncStatus. Do not use this component in isolation without a parent providing these props.' This one-liner will prevent future misuse.

#### note: Collision detection uses If-Match header correctly but lacks server-side test assertion
**Location:** src/backend/api/notes.py:373-408
**Quote:**

```
// Collision detection: validate If-Match header if provided
    if if_match is not None and if_match != current_revision_id:
```

**Read:** The backend correctly implements optimistic locking: it computes the current revision_id, compares it to the If-Match header, and returns 409 if they don't match. The logic is sound.
**Concern:** I cannot verify the backend's collision detection works correctly without seeing the test scenarios. The code is correct as written, but I want to flag: this is a critical path for data integrity. If the collision detection fails, Kohl could silently lose edits or overwrite concurrent work. The code looks good, but it needs thorough test coverage.
**Request:** No code change. This is a note for the Mad Hatter and the Caterpillar (if testing): verify that test scenarios cover (1) successful save with matching If-Match, (2) 409 when If-Match doesn't match, (3) successful save without If-Match (backward compatibility), (4) collision detection with concurrent saves from multiple tabs/sessions. The code is correct; just make sure the tests are thorough.

#### suggestion: LocalStorageBuffer interface defined but unused in useBootNotes
**Location:** frontend/src/useBootNotes.ts:29-33
**Quote:**

```
interface LocalStorageBuffer {
  title: string;
  body: string;
  tags: string[];
  lastSyncedAt: string;  // ISO8601 timestamp from last successful save
}
```

**Read:** The LocalStorageBuffer interface is defined at the top of useBootNotes.ts but is never used in the function body. It's included in the JSDoc but the implementation doesn't apply it.
**Concern:** Dead code (or unreachable design). This suggests the interface was defined in anticipation of merging logic that isn't implemented. It creates reader confusion: why is this interface here if it's not used? Future readers will ask whether it's obsolete or planned for a later phase.
**Request:** Either use LocalStorageBuffer in the actual merge logic (implement the promised merge strategy), or delete it. If the interface is truly unused, remove it to avoid confusion. If the merge logic will be added in a future sprint, add a TODO comment explaining when it will be implemented: '// TODO: implement per-note buffer merging in ticket-XXX'.

### Approvals

- The boot reconciliation flow (useBootNotes hook + Editor's conflict UI on load) is well-structured. The separation of concerns is clear: App handles fetching the list of persisted notes, Editor handles loading individual note state and reconciling with keystroke buffers.
- The collision detection implementation (revision_id computation, If-Match header validation, 409 response with server state) is correct and thoughtfully designed. The deterministic hashing ensures idempotent saves and guards against race conditions in multi-tab scenarios.
- Audit trail logging is comprehensive. The AuditLog model captures full-state snapshots, collision flags, and state hashes, providing strong forensic completeness for future investigation of data integrity issues.
- localStorage debouncing via useLocalStorageDebounce is a solid pattern — reduces thrashing of storage writes without losing keystroke data. The 2-second debounce window is appropriate for interactive editing.
- The merge UI (both for boot-time conflicts and save-time collisions) is user-friendly and gives Kohl clear options: keep her changes or use the server version. The UI shows timestamps and previews so she can make an informed decision.

### Cross-domain references

- This implementation implies a backend contract (contract-note-01KRY0B8 on revision-id computation) that should be verified by the Cat — ensure the collision detection design aligns with the architectural intent and doesn't have unintended side effects.
- The audit trail table (AuditLog) and collision logging should be reviewed by the Dormouse for observability — currently there are no structured logs emitted when saves happen or collisions occur. Consider adding logging at save time so production behavior is visible.
- Test scenarios 253 and 255 (referenced in the code) need to be verified to exist by the Hatter — confirm they match the boot reconciliation and collision detection behavior implemented in the Editor.
