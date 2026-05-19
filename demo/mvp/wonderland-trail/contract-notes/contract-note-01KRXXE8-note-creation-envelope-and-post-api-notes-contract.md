## Contract Note 015: Note creation envelope and POST /api/notes contract

**GUID:** 01KRXXE8JWDQGP5PMCWW58AT9G
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

n/a, fresh feature thread

**Proposed Change:**

POST /api/notes request {title: string (required, non-empty), body: string (optional, max 50K), tag_ids: number[]}. Response 200: {id, title, body, tags: [{id, name}], created_at, updated_at, version}. The response includes server-assigned id, timestamps (ISO8601), and opaque version identifier (hash of saved state) for collision detection.

**Source:** Your question 1 + Feature 001 (Kohl creates and saves notes) + ADR-004 (keystroke buffer recovery).

**Frontend Impact (Tweedledee):**

Send {title, body, tag_ids} from editor on Save button click. Expect response with id (store for subsequent PATCH), version (cache for collision detection), timestamps (update UI). On success: clear localStorage, update editor state with returned id. Component tracks {isSaving: bool, error: string | null} for UX.

**Tweedledee Response:**

Approved. I'll structure EditorState to hold {id: string | null, title, body, tags: {id, name}[], version: string, isSaving: bool, error: string | null}. On mount, id is null (new note). Save button click sends POST with {title, body, tag_ids: tags.map(t => t.id)}. On 200 success, I update id, version, and clear localStorage buffer. Version caching allows me to detect collisions on next PATCH. Confirmed: response includes id, version, timestamps — I need all three.

**Backend Impact (Tweedledum):**

Accept POST with above shape. Validate title non-empty, tag_ids exist, no duplicates. Return fully-formed response with id, version, timestamps.
