## Implementation 031: Tag input UI and integration in editor

**GUID:** 01KRXY39GCF2Z5ND55BBDKYREE
**Side:** frontend
**Ticket:** add-tag-inputs-to-editor-ui
**Contract:** note-creation-envelope v1 (POST /api/notes accepts tag_names: string[], response includes tag_names and tag_ids per contract-note-01KRXRTT)
**Ready for review:** yes

**Approach:**

TagInput component accepts user free-text tag entries (type + Enter or click Add), displays as removable chips, validates (trims whitespace, rejects empty/duplicates). Editor integrates TagInput, persists tags to localStorage alongside title/body, sends tag_names array on save. No tag autocomplete; free-text only.

**UI States Implemented:**
- idle: user can type in tag input field
- added: tag appears as removable chip after Enter or Add click
- error-recoverable: duplicate tag attempt (already in list) — rejected silently, field cleared
- empty-tag-attempt: whitespace-only input — rejected, field cleared
- save-success: tags included in note save payload, cleared from client state on success

**Client State:**

Editor state includes tags: string[] array of user-entered tag names. Persisted to localStorage as part of editor_draft JSON payload. On mount, restored from localStorage if present. On tag change (add/remove), written to localStorage. On successful save, cleared from state and localStorage. Tag IDs from backend response are informational only; client only stores/uses tag names.

**Files:**
- frontend/src/TagInput.tsx: tag input component with add/remove handlers, whitespace trimming, duplicate detection
- frontend/src/Editor.tsx: integrated TagInput, added handleTagsChange, updated localStorage + save payload
- frontend/src/api.ts: already defines contract with tag_names in request and response

**Known Limitations:**
- No tag autocomplete/dropdown — free-text only (future fast-follow could add GET /api/tags endpoint)
- No frontend tag validation — backend enforces constraints (max 100 chars), user sees error on save if tag too long
- No optimistic persistence — tags only saved when full note saves; failure means re-entry (but state preserved in localStorage)
