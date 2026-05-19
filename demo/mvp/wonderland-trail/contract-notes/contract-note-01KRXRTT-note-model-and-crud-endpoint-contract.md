## Contract Note 001: Note model and CRUD endpoint contract

**GUID:** 01KRXRTTX8132D8F41PJS7GRK2
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

HelloMessage placeholder (id, text, created_at); POST /api/messages echo endpoint

**Proposed Change:**

Replace with Note model (id, title, body, created_at, updated_at, tags); CRUD endpoints: POST /api/notes (create), GET /api/notes (list), GET /api/notes/{id} (read), PUT /api/notes/{id} (update), DELETE /api/notes/{id} (delete). All timestamps in ISO8601. Tags initially stored as JSON array (denormalized) — normalization deferred to v2 if tag filtering/counting becomes load.

**Source:** Feature 001: Kohl can create and save experimental notes with title and body. Requires full CRUD to support creation, listing, editing, deletion.

**Frontend Impact (Tweedledee):**

Tweedledee frontend impact: POST /api/notes request body will be {title, body, tag_ids: string[]} (tag IDs or names, clarified in tag-creation-contract). Response must include persisted {id, title, body, created_at, updated_at, tags: TagObject[]} so editor can update component state and localStorage after save. Listing endpoint (GET /api/notes) must return notes in reverse chronological order, which I will consume for the search/list view (fast-follow but contract shape needed now).

**Backend Impact (Tweedledum):**

Schema change: Note table with (id PK, title TEXT NOT NULL, body TEXT, created_at DATETIME, updated_at DATETIME, tags JSON). Endpoints validate title non-empty, body optional, tags as stringarray. Listing returns reverse chronological (updated_at DESC). No auth layer v1 (single-device assumption per requirements). Migrations: straightforward schema swap from hello_messages to notes table.
