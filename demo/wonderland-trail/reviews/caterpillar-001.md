# Review: Feature 002 — Kohl can organize notes with tags and read them in markdown preview

**GUID:** 01KRXSZ1K8DEN7FHW0FVDKZZC7
**Verdict:** accept
**Reviewer's pace:** thorough

## Summary

M8 review of Feature 002 across all constituent tickets: Backend CRUD endpoints (ticket-006), Editor keystroke buffer (ticket-007), Markdown preview (ticket-008), and Tag input (ticket-009). Cross-ticket coherence check passed. Implementation matches contracts. All acceptance criteria met. Feature is ready for merge.

## Cross-Ticket Coherence

✅ **Contract integrity verified.** Contract-note-01KRXRTT specifies the POST /api/notes envelope — request: `{title: str, body?: str, tag_names?: str[]}`, response: `{id: int, title: str, body: str, tag_names: str[], tag_ids: int[], created_at: ISO8601, updated_at: ISO8601}`.

- Backend: NoteCreate enforces the request schema. NoteResponse serializes the response schema. create_note() returns 201 with full note.
- Frontend: api.ts createNote() calls POST /api/notes with the same envelope. Editor.tsx calls it with the correct payload. TagInput.tsx feeds tag_names into state.
- Result: no contract drift, no field name mismatches, no orphaned fields.

✅ **App entry point is wired.** App.tsx renders EditorLayout (not the old Editor placeholder). EditorLayout composes Editor and Preview side-by-side with proper state threading (onBodyChange callback). Users see the full feature, not a skeleton.

✅ **Tag association is atomic.** All three layers (backend schema, endpoint, frontend state) handle tags as part of the same save envelope. No separate API calls needed. Frontend sends tag_names, backend auto-creates missing tags and returns tag_ids, frontend can use both for display and future updates.

## Findings

None. All acceptance criteria met. All contracts honored. No blocking issues.

## Approvals

**Backend Implementation (notes.py, models.py, main.py)**

- Schema design is sound: Note.body is Text NOT NULL with default='', correctly implementing the optional-in-request, non-NULL-in-storage contract. note_tags association table uses CASCADE delete on note_id (correct) but NOT on tag_id (correct — tags are shared). The cascade semantics are documented and prevent orphaned tags.

- CRUD endpoints cover all acceptance criteria from ticket-006:
  - POST /api/notes creates note with auto-assigned id, returns 201, enforces title required + non-empty
  - GET /api/notes lists all in reverse chronological order (secondary sort by id DESC for determinism)
  - GET /api/notes/{id} reads one, returns 404 if missing
  - PUT /api/notes/{id} updates fields atomically, returns 404 if missing
  - DELETE /api/notes/{id} removes note, returns 404 if missing
  - POST /api/notes/{id}/tags associates tag by name, auto-creates if missing, idempotent
  - DELETE /api/notes/{id}/tags/{tag_id} removes association, validates both targets, returns 404 if missing

- Tag association is atomic and resilient: _associate_tags() deduplicates tag_names before associating (prevents UNIQUE constraint violations from duplicate input). Uses db.flush() to ensure tag IDs are assigned before association. POST /api/notes/{id}/tags idempotently appends a tag (already-associated tag is silently skipped).

- Timestamp handling is rigorous: Note.to_dict() ensures all timestamps are timezone-aware UTC ISO8601 strings with Z suffix. Handles the case where SQLite returns naive datetimes (assumes UTC). All responses have consistent format. No naive timestamps leak out.

- Error handling is appropriate: Pydantic Field constraints reject invalid input before endpoint code runs (automatic 400 response). HTTP status codes are correct (201, 200, 204, 404). No silent failures or misleading status codes.

**Frontend Implementation (Editor.tsx, Preview.tsx, TagInput.tsx, api.ts)**

- Editor keystroke buffer is correctly implemented: Writes {title, body, tags} to localStorage on every keystroke. Restores from localStorage on mount. Clears after successful save. If localStorage parsing fails, gracefully removes the key and starts fresh. Buffer survives page reload.

- Validation is correct: Editor validates title non-empty and <= 255 chars before sending. Validates body <= 16384 chars. Displays validation errors inline, preserves state for retry. No validation errors leak to console.

- Save flow is atomic from user perspective: Single POST /api/notes call with {title, body, tag_names}. On success, clears localStorage and resets editor. On error, preserves state and shows error message for manual retry. Error handling is appropriate for the single-user no-auth scope.

- Preview pane is XSS-safe and handles degradation: Uses DOMPurify.sanitize() + marked for markdown parsing. Catches parse errors and displays inline error message rather than crashing. Empty body renders as empty (no error state). useMemo hook avoids unnecessary re-parsing.

- TagInput component correctly implements contract: Accepts {tags: string[], onTagsChange} props. Users type, press Enter or click Add. Input is trimmed, duplicates rejected, empty strings rejected. Remove button removes tags. Parent Editor threads into state and localStorage. Tag flow is cohesive.

- API wrapper is clean: api.ts exports createNote(), listNotes(), readNote(), updateNote(), deleteNote() functions. Each wraps fetch + JSON + error handling. Frontend code is free of HTTP implementation details.

**Integration (App.tsx, EditorLayout.tsx, main.py)**

- App entry point is wired: App.tsx imports EditorLayout and renders it as root. EditorLayout composes Editor and Preview with proper state passing. No orphaned components. Users see the full feature.

- CORS is correctly configured in main.py: allow_origins=["http://localhost:5173"] permits the Vite dev server to call the backend API. Standard for development.

- Test fixtures are in place: conftest.py exports db_engine, db_session, client fixtures. TestClient wraps the FastAPI app with in-memory SQLite. Tests can run against fresh DB without disk I/O.

## Done

All acceptance criteria met. All contracts honored. Cross-ticket coherence verified. Feature is ready to merge.
