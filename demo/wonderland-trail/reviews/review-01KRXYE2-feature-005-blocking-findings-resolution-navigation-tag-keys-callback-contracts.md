## Review 032: Feature 005 blocking-findings resolution: navigation, tag keys, callback contracts

**GUID:** 01KRXYE238P9VG1MA05E10C6XB
**Files reviewed:** frontend/src/App.tsx, frontend/src/NoteList.tsx, frontend/src/EditorLayout.tsx, frontend/src/Editor.tsx, src/backend/models.py, tests/test_tag_scenarios.py
**Verdict:** accept

### Approvals

- Navigation contract fixed cleanly: selectedNoteId threads from NoteList click → App state → EditorLayout prop → Editor.useEffect hydration. The flow is now explicit and testable.
- React keys use tag_ids (stable identifiers) instead of array indices. The invariant (tag_names[i] ↔ tag_ids[i] correspondence guaranteed by models.py:to_dict()) is sound and documented.
- Callback prop contract now matches implementation: onEdit(noteId) is declared and used as specified. Unused onNoteClick prop removed. Contracts are coherent.
- Cross-ticket coherence verified: backend response shape (NoteResponse includes tag_names and tag_ids, returned by list_notes and read_note endpoints per contract-note-014 and contract-note-015) matches frontend assumptions (NoteList.tsx reads both fields, Editor.tsx renders and persists both). No field-name mismatches or implicit contracts.
- Test scenarios document edge cases with precision (whitespace normalization, case sensitivity, concurrent tag creation, shared tag preservation across note deletion, pagination determinism, body_preview truncation). All severity levels assigned; scenarios are actionable for Hatter.
- EditorLayout properly distinguishes create (noteId=null) from edit (noteId=provided) flow: handleEditorSave navigates back to list, loadNote restores from server on mount. The distinction is explicit and aligns with Editor component's acceptance criteria.

### Cross-domain references

- Tag normalization semantics (whitespace, case sensitivity) should be locked in contract-note-005 before v1 ships — the test scenarios flag ambiguity, but backend auto-create behavior and frontend validation expectations should be formalized.
- Feature scope clarification needed: 'adds tags while editing or after creation' — does 'after creation' include inline tag editing in NoteList (add/remove chips in place), or only via EditorLayout? This is a UX/product decision; backend supports both. Current implementation is editor-only. Recommend Alice + Rabbit clarify before Feature 005 is marked 'done.'
