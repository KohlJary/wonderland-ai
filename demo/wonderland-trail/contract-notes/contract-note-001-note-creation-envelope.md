# Contract Note: Note creation envelope and POST /api/notes contract

**GUID:** 01KRXX9X-tweedle-substrate-thread-001
**State:** proposed
**Contract Version:** (unlocked)

## Current Shape

n/a — fresh feature thread for substrate v1

## Proposed Change

POST /api/notes request:
```json
{
  "title": "string (required, non-empty)",
  "body": "string (optional, max 50K)",
  "tag_ids": "[number]"
}
```

Response 200:
```json
{
  "id": "number",
  "title": "string",
  "body": "string | null",
  "tags": [{"id": "number", "name": "string"}],
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "version": "string (opaque hash of saved state)"
}
```

## Source

Tweedledum's question 1: "Note creation—POST /api/notes with {title, body, tags} should return full note {id, title, body, tags, created_at, updated_at}?"

Feature 001 (Kohl creates and saves notes)
ADR-004 (keystroke buffer recovery)

## Frontend Impact (Tweedledee)

Send {title, body, tag_ids} from editor on Save button click. Expect response with:
- id: store to switch from POST to PATCH on next save
- version: cache for collision detection in GET hydration
- timestamps: update UI to show when note was created/modified
- tags: update editor tag state after save

On success: clear localStorage, update editor state with returned id. Component tracks {isSaving: bool, error: string | null} for UX feedback (disable Save button while isSaving, show error message on failure).

## Backend Impact (Tweedledum)

Accept POST with above shape. Validations:
- title: non-empty (400 if missing)
- body: optional, max 50K
- tag_ids: array of valid tag IDs (400 if invalid or duplicate)

Return fully-formed response with server-assigned id, timestamps (ISO8601), and version identifier for collision detection (per ADR-004).

## Resolution

Proposed — awaiting your confirmation that this matches your endpoint shape and validation strategy.
