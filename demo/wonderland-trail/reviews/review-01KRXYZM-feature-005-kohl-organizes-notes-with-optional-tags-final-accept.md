## Review 039: Feature 005: Kohl organizes notes with optional tags — FINAL ACCEPT

**GUID:** 01KRXYZMXJ7VC4D3PTWJCVV5JQ
**Files reviewed:** src/backend/api/notes.py, src/backend/models.py, tests/test_notes_edge_cases.py, tests/test_tag_scenarios.py
**Verdict:** accept

### Approvals

- SQL LIKE escaping (_escape_like_pattern) correctly prevents % and _ wildcard metacharacters from being interpreted as search operators. Test coverage for special-character queries is solid.
- Tag name normalization (_normalize_and_validate_tag_names) enforces whitespace stripping and rejects empty-after-strip entries with a clear 400 error. This blocks the silent-wrongness scenario (whitespace-only tags appearing in results).
- Contract-note-01KRXYD0 (tag-case-sensitivity) is explicitly documented in models.py and enforced in both tag creation and association paths. Case-sensitive deduplication is locked in.
- Test assertions have been clarified from permissive (accepting multiple outcomes) to specific (asserting exactly 2 tags for duplicate input, case-sensitive dedup for case-variants, rejection for whitespace-only). This removes ambiguity in acceptance criteria.
- Frontend navigation contract (selectedNoteId threading through App → EditorLayout → Editor) has been verified in prior rounds and is functionally complete. Core end-to-end user flow works: click note in list → edit tags in editor → save → tags persist.
- Tag key generation (using stable tag_ids instead of array indices) has been fixed and verified. React rendering is correct.
- Cross-ticket coherence verified: backend returns {tag_names, tag_ids} in aligned order (names and IDs at matching indices); frontend consumes correctly in NoteList rendering.
