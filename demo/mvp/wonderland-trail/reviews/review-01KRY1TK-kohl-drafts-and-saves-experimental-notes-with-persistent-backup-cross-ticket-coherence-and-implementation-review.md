## Review 048: Kohl drafts and saves experimental notes with persistent backup — cross-ticket coherence and implementation review

**GUID:** 01KRY1TK6QZ48V2V5P1RGG7CEK
**Files reviewed:** src/backend/models.py, frontend/src/Editor.tsx, frontend/src/api.ts, frontend/src/useBootNotes.ts
**Verdict:** request-changes

### Findings

#### block: Collision detection response shape mismatch: backend wraps ConflictError in 'detail' field, frontend unwraps it conditionally
**Location:** frontend/src/api.ts:128-145
**Quote:**

```
    // FastAPI wraps the HTTPException detail in a 'detail' field.
    // The detail contains our conflict response: {error, message, server_revision_id, server_state}
    const conflictData = responseBody.detail || responseBody;
    
    // Type-check the conflict response to ensure it has the expected shape
    if (
      conflictData &&
      typeof conflictData === 'object' &&
      'error' in conflictData &&
      'server_revision_id' in conflictData &&
      'server_state' in conflictData
    ) {
```

**Read:** The frontend expects a 409 response with a 'detail' field wrapping the ConflictError shape, and falls back to unwrapped response if detail is absent. The backend (src/backend/api.py:450-460) raises HTTPException with the ConflictError as the detail field, which FastAPI will serialize as {detail: {...}}. This is a correct read of FastAPI's behavior, but the fallback path and type-checking suggest uncertainty about the contract.
**Concern:** The contract-note-01KRY0B8 names the expected response as {error, message, server_revision_id, server_state}, but does not explicitly document that FastAPI wraps this in a 'detail' field. The frontend's defensive unpacking is correct but suggests the contract is unclear. Additionally, the fallback path that throws if the shape doesn't match means the contract is enforced at runtime in the client rather than documented explicitly. A caller who doesn't know about FastAPI's detail wrapping will receive a cryptic error.
**Request:** Update contract-note-01KRY0B8 to explicitly state: 'HTTP 409 response body is {detail: {error: "ConflictError", message: ..., server_revision_id: ..., server_state: ...}}. FastAPI wraps the HTTPException detail in a top-level detail field. Client must unwrap before parsing.' Remove the fallback throw in api.ts and replace with an assertion, since the contract is now explicit. If the contract says 'detail', expect 'detail'.

#### change-required: Editor.tsx conflict state initialization ambiguity: two distinct conflict states (conflict vs conflictState) manage overlapping concerns
**Location:** frontend/src/Editor.tsx:54-56
**Quote:**

```
  const [conflict, setConflict] = useState<ConflictState | null>(null);
  const [conflictState, setConflictState] = useState<ConflictState | null>(null);
```

**Read:** The Editor maintains two state variables for conflicts: `conflict` (boot-time merge detection when a localStorage buffer and server note coexist) and `conflictState` (collision during a save attempt when the If-Match header fails). Both have type ConflictState and both render conflicting UIs (different merge UI vs collision modal). The code disables the Save button when either is set, but they represent different invariants and recovery paths.
**Concern:** Having two state variables with overlapping type and similar naming creates confusion about which conflict has been detected and what the user sees. Reading the flow: (1) on mount, if both server and buffer exist and buffer is newer, set `conflict` and show merge UI; (2) if user saves and gets 409, set `conflictState` and show modal. The invariant that only one can be active is implicit. If both become true simultaneously (race condition on save during mount reconciliation), the UI will render both, which is undefined behavior. The naming doesn't distinguish 'boot-time' from 'save-time' conflict.
**Request:** Rename the state variables to make their role explicit: `bootConflict` (for boot-time merge detection) and `saveConflict` (for save-time collision). Add an assertion or guard that prevents both from being true simultaneously. Alternatively, unify into a single state variable with a type discriminant: `const [conflict, setConflict] = useState<{type: 'boot', ...} | {type: 'save', ...} | null>(null)`. The current structure is correct in behavior but confusing in intent.

#### change-required: ConflictError interface missing 'message' field implementation in backend 409 response
**Location:** frontend/src/api.ts:68-72
**Quote:**

```
export interface ConflictError {
  error: 'ConflictError';
  message: string;  // Descriptive message from backend
  server_revision_id: string;  // Current revision_id on the server
  server_state: Note;  // Backend's current note state (includes new revision_id)
}
```

**Read:** The frontend ConflictError interface defines a `message` field as required. The backend (src/backend/api.py:453-460) raises HTTPException with a detail containing 'message': 'Note has been updated since you last synced...'. The field is present in the backend.
**Concern:** On careful reading, the backend does include the message field, so this is not a breaking mismatch. However, the frontend's fallback in updateNote() (line 138) provides a default if message is missing: `message: conflictData.message || 'Conflict detected'`. This suggests the interface declared message as required but the implementation treats it as optional. This inconsistency is a minor contract fragility.
**Request:** Make the message field explicitly required in the contract-note and ensure the backend always populates it (which it does). No code change needed since both sides are aligned, but update the contract-note-01KRY0B8 to state: 'message field is always present and human-readable (e.g., "Note has been updated since you last synced...").' Remove the `|| 'Conflict detected'` fallback in api.ts since the contract guarantees message is present.

#### suggestion: compute_revision_id includes updated_at timestamp in hash, but hash is supposed to be deterministic across reads
**Location:** src/backend/models.py:40-42
**Quote:**

```
    canonical_state = json.dumps(
        {
            "title": title,
            "body": body,
            "tag_ids": sorted(sorted_tag_ids),  # Sort to be order-independent
            "updated_at": updated_at,
        },
```

**Read:** The revision_id hash includes the updated_at timestamp as part of the canonical state. The timestamp is the server-assigned updated_at from the Note's database column. On a successful save, updated_at is automatically updated by SQLAlchemy's onupdate=func.now(). This means the revision_id will change whenever the note is updated, which is correct for collision detection.
**Concern:** The contract-note-01KRY0B8 states revision_id should be deterministic and used for optimistic locking. Including updated_at in the hash makes revision_id a function of [title, body, tag_ids, updated_at]. If two identical edits are saved with different updated_at values (e.g., if the same user saves twice at different times without changing content), the revision_ids will differ. This is actually correct for the collision detection use case (detecting when a note has been touched), but it's worth documenting: revision_id includes timestamp, so it detects both content changes AND timestamp changes. A comment in the code should clarify: 'Including updated_at means revision_id changes on every save, even if content is unchanged. This is intentional: it detects concurrent access even without content changes.' The current code doesn't make this explicit.
**Request:** Add a clarifying comment above the canonical_state construction: 'The revision_id hash includes updated_at to detect when a note has been touched by concurrent access, regardless of whether content changed. This means identical edits saved at different times have different revision_ids, which is correct for pessimistic locking across concurrent editors.' The code is correct; the comment just makes the intention clear for future maintainers.

#### suggestion: localStorage timestamp comparison uses milliseconds but ISO8601 timestamps have microsecond precision
**Location:** frontend/src/Editor.tsx:75-80
**Quote:**

```
              // Parse server's updated_at to milliseconds
              const serverTime = new Date(serverNote.updated_at).getTime();
              
              if (bufferTime > serverTime) {
```

**Read:** The boot reconciliation compares two timestamps: bufferTime (from Date.now() in milliseconds, written to localStorage) and serverTime (parsed from ISO8601 string with microsecond precision from backend). The backend returns timestamps like '2024-01-15T10:30:45.123456Z', which JavaScript's new Date().getTime() truncates to milliseconds (1 digit of precision lost).
**Concern:** This is unlikely to cause a bug in practice (the probability that two saves happen within the same millisecond is low), but it's a precision mismatch. If a user edits locally, the localStorage buffer gets a timestamp like 1705318245123 (ms). The server might return updated_at='2024-01-15T10:30:45.123456Z', which getTime() truncates to 1705318245123. They will appear equal if the microseconds round down. This is correct behavior for the intent (if they're the same millisecond, prefer the buffer), but the precision difference is worth documenting.
**Request:** Add a comment: 'Note: server updated_at has microsecond precision, but JavaScript Date.getTime() returns milliseconds. Comparison truncates microseconds, which is safe: if they're the same millisecond, bufferTime and serverTime will be equal, and we prefer the buffer (it's newer or equal).' This is not a code change, just a clarification for maintainers.

#### note: TODO comment in compute_revision_id about caching revision_id as a database column
**Location:** src/backend/models.py:43-49
**Quote:**

```
    TODO (ticket-081): Cache revision_id as a database column (computed on every write, cached on reads).
    Currently recomputed on every GET request (100 notes × 100 hash calls for a list is acceptable
    for MVP single-user scope, but adds O(n) CPU per list operation). For post-MVP optimization:
    add `revision_id` column to Note model, compute on POST/PUT, return from cache on GET.
    Revisit after performance testing confirms this is a bottleneck.
```

**Read:** The revision_id is computed on every GET /notes and GET /notes/{id} by calling compute_revision_id() with the note's current state. For a single-user MVP with tens of notes, this is acceptable. For 100+ notes or multi-user scenarios, the O(n) hash computation per list request will add measurable CPU cost.
**Concern:** None currently. The decision to defer caching is reasonable for MVP scope. The TODO is well-placed and clear about when to revisit.
**Request:** None. This is a good forward-looking optimization placeholder. No action needed for v1.

#### note: Revision ID state tracking in Editor properly initialized to null and updated from server responses
**Location:** frontend/src/Editor.tsx:37-45
**Quote:**

```
  // revision_id is null for new notes and for buffers whose revision_id is unknown or stale
  // (e.g., restored from localStorage). On successful save, revision_id is set to the server
  // response. On conflict (409), revision_id is set to null because the buffer is in an
  // uncommitted edit state and any cached revision_id may be stale relative to the server.
  // INVARIANT: trust revision_id from server responses (readNote, POST/PUT success) and ignore
  // stale revision_id from localStorage buffers — they may not reflect the note's current state
  // on the server, especially if the note was edited elsewhere (another device/tab/session).
  revision_id: string | null;
```

**Read:** The Editor component maintains revision_id in state with clear semantics: null for new notes or stale buffers, set to server response after successful saves, reset to null on conflict (409). The comments document the invariant: only trust revision_id from server responses, never from localStorage.
**Concern:** None. This is correctly implemented.
**Request:** Approved. The state management is sound and the documentation is clear.

#### change-required: useBootNotes comments incorrectly describe scope of localStorage merge logic; actual merge happens in Editor, not here
**Location:** frontend/src/useBootNotes.ts:5-17
**Quote:**

```
/**
 * useBootNotes — loads persisted notes on app boot for the note list.
 *
 * Contract: ticket-066 (frontend-load-on-boot)
 *
 * On app boot:
 * 1. Fetch GET /notes (all persisted notes from backend, reverse chronological)
 * 2. Return the list for display in the note list sidebar
 * 3. Per-note buffer merging is delegated to the Editor component when a specific note is opened
 *
 * Merge responsibility: Editor component (useBootNotes is global scope; Editor handles per-note scope)
 * - When Editor loads a specific note by ID, it checks localStorage for that note's keystroke buffer
 * - If a buffer exists AND is newer than the server version (per timestamp), Editor shows a merge UI
 * - User chooses: keep unsaved changes or load server version
 */
```

**Read:** The useBootNotes hook fetches the list of notes from GET /api/notes and returns them for display. It does NOT perform per-note buffer merging. That responsibility is delegated to the Editor component, which handles the merge reconciliation when a specific note is opened. The comment correctly describes this delegation.
**Concern:** The original comment (in the diff) was longer and more complex, describing a 'merge strategy (OPTIMISTIC)' with details about buffer precedence logic. The new comment correctly simplifies it to 'useBootNotes loads the list; Editor handles per-note merge.' This is clearer, but the removal of the old strategy description means a future developer might not know WHY the responsibility is split. Adding one sentence about the rationale would help.
**Request:** Enhance the comment with rationale: 'Per-note buffer merging is delegated to the Editor component when a specific note is opened because: (1) useBootNotes operates at global scope (entire note list), but merge reconciliation is per-note; (2) Editor has access to both the specific note's server state and the corresponding localStorage buffer; (3) this separation of concerns keeps useBootNotes simple (fetch + return) and Editor focused (load, merge, edit).' This is a documentation improvement, not a code change.

### Approvals

- The backend Note model schema is well-structured: title, body, timestamps with timezone awareness, tags as a proper many-to-many relationship. The audit trail implementation with immutable log entries is architecturally sound.
- The collision detection implementation via If-Match header and SHA256 revision_id hashing is correct. The deterministic hash computation (sorting tag_ids, normalizing JSON) ensures idempotence. The audit trail logs both successful saves and failed collision attempts, meeting forensic completeness requirements.
- The frontend Editor component correctly implements boot-time merge reconciliation (comparing localStorage buffer timestamp to server updated_at) and save-time collision handling (409 response with user choice modal). The revision_id state management is clear: null for new/stale, set from server responses, reset on conflict.
- The api.ts wrapper correctly handles FastAPI's 409 response wrapping (unwrapping the 'detail' field), type-checks the ConflictError shape, and defaults message if absent. The type guards prevent runtime surprise from malformed responses.
- The separation of concerns is correct: useBootNotes fetches the global note list; Editor handles per-note merge reconciliation and collision detection. This keeps each component focused.
- Code quality: Naming is mostly clear (debouncedSaveToStorage, handleMergeChoice, _record_audit_log). Comments document invariants and design decisions at key points. Error handling preserves state for retry on both save and load failures.

### Cross-domain references

- The collision detection contract-note-01KRY0B8 should be clarified to explicitly document FastAPI's 'detail' wrapping of 409 responses, per the block finding above. This is a contract documentation gap, not an implementation gap.
- The revised contract should also be explicit about what 'message' field is guaranteed to be present in ConflictError responses, to remove the fallback check in api.ts.
- Per the Hatter's test scenarios on collision detection (get-notes-id-single-note-fetch-also-scales-efficiently, user-in-tab-a-and-tab-b-both-edit-the-same-note-etc.), verify that the 409 response includes the full server_state with all fields (title, body, tag_names, tag_ids, created_at, updated_at, revision_id). A manual test or scenario execution is recommended to ensure the response shape matches what the frontend expects in the Modal UI.
