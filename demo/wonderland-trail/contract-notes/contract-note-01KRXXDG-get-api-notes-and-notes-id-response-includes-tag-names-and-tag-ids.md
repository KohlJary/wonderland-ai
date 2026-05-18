## Contract Note 014: GET /api/notes and /notes/{id} response includes tag_names and tag_ids

**GUID:** 01KRXXDG2W1XWV4A8W1YGAVCZA
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

Implicit in contract-note-004 (note creation response shape); not explicitly stated for GET responses. Implementation in notes.py shows both endpoints return tags, but contract should be explicit.

**Proposed Change:**

Formalize GET /api/notes and GET /api/notes/{id} response envelope to explicitly include tag_names: [string] and tag_ids: [integer] alongside other fields (id, title, body, created_at, updated_at).

**Source:** Feature 002 (Kohl organizes notes with optional tags) / Ticket 034 (Display tags grouped in note list view) requires frontend to render tag badges for each note in list view. Frontend needs explicit contract that these fields are available in list-fetch responses.

**Frontend Impact (Tweedledee):**

Editor, Search, and future NoteList views all consume tag_names to render tag badges and tag_ids for future autocomplete features. Current implementation in api.ts assumes these fields exist in Note interface; formalizing the contract prevents runtime surprises.

**Backend Impact (Tweedledum):**

(Tweedledum to fill in)
