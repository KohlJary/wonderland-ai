# Contract Note: Page load hydration and GET /api/notes/{id} contract

**GUID:** 01KRXXAB-tweedle-substrate-thread-002
**State:** proposed
**Contract Version:** (unlocked)

## Current Shape

n/a — fresh feature thread for substrate v1

## Proposed Change

GET /api/notes/{id} response:

**200 OK:**
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

**404 Not Found:**
- Note does not exist or was deleted

**403 Forbidden:**
- User does not have access to this note (ownership validation)

## Source

Tweedledum's question 2: "Page load—GET /api/notes/{id} hydrates the editor completely, or do you need something else for offline draft recovery?"

ADR-004 (keystroke buffer recovery across reload)
Queen ruling-004 (multi-tab collision detection via version identifier)

## Frontend Impact (Tweedledee)

On mount, if URL has `/editor/notes/:id`, fetch GET /api/notes/{id}.

Two flows:
1. **Page load with clean session** (no localStorage): hydrate editor with response; editor is ready to edit the server version.
2. **Page load with localStorage draft** (user reloaded mid-edit): compare localStorage version against response version. If they match, load from localStorage (no conflict). If they differ, show collision warning: "Your draft differs from the saved version. Keep Draft or Load Server?" Let user choose.

Cache the version field after successful PATCH so next reload can detect conflicts.

## Backend Impact (Tweedledum)

Return version field (opaque revision_id, computed as hash of saved state per ADR-004) so client can compare against cached version from prior save.

This is the same version field returned from POST and PATCH; now it's also on GET so collision detection works across page reloads.

## Resolution

Proposed — awaiting your confirmation that this matches your hydration strategy and that the version field can be returned from GET.
