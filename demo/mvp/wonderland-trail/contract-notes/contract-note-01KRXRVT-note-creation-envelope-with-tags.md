## Contract Note 004: Note Creation Envelope with Tags

**GUID:** 01KRXRVTH7NW2PJTRN0CRKATHG
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Backend ticket 006 specifies POST /notes endpoint returns note object with id, but the request envelope for sending tags is unspecified.

**Proposed Change:**

Define the POST /notes request body shape: does the frontend send {title, body, tags: [string]} or {title, body, tag_ids: [number]}, or should tags be sent in a separate call? Similarly, for PUT /notes/:id updates, can the payload include tags, or only via the separate /tags endpoints?

**Source:** Frontend tickets 007 (editor with Save button), 008 (preview), and 009 (tag input) all assume a Save flow but the exact envelope for sending tags is unspecified. This affects client state shape (what does the editor component hold?) and error handling (is save atomic or multi-step?).

**Frontend Impact (Tweedledee):**

Confirmed: I will buffer tag_names as strings in editor component state, send as {title, body, tag_names: string[]} in POST /notes request, and accept the response with full note object including tag_names and tag_ids. This gives me both fields for display and future autocomplete. Error handling: if POST fails with 400 (e.g., tag_name exceeds length), I show user-facing error and keep the draft in editor state so work isn't lost. Single-envelope atomicity matches my UX expectation — user taps Save once, everything ships or nothing does.

**Backend Impact (Tweedledum):**

Backend supports single-envelope POST /notes: request body is {title: string, body: string, tag_names: [string]}. All three fields are included in the same request; the operation is atomic (single transaction). Request validation: title must be non-empty string (1-500 chars); body optional (0-50K chars); tag_names is array of non-empty strings (0-20 tags, each 1-100 chars). Response (on success, 200): {id, title, body, tag_names: [string], tag_ids: [integer], created_at, updated_at}. This allows Tweedledee to: (a) send one envelope on save, (b) get back both tag names and IDs so client can cache for display/autocomplete, (c) know the operation completed atomically. If any tag_name is invalid (e.g., exceeds length), the entire POST fails with 400 before any write. PATCH /notes/:id uses the same envelope shape for updates. Both endpoints return the full persisted note, allowing client to reconcile localStorage with server state.
