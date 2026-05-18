## Scenario 006: Kohl saves her first experimental note and refreshes the page — the note survives

**GUID:** 01KRXSC2B76HKK0C1NK7MRJY5V
**Severity:** breakage

**Setup:**

Kohl opens the editor for the first time. The page is fresh, no prior notes exist in the database. She has entered a title 'Initial RNA folding experiment' and body 'Started with a 50-nucleotide sequence...' in the editor form. The Save button is ready to be clicked.

**Trigger:**

Kohl clicks Save. The editor sends POST /api/notes with {title: 'Initial RNA folding experiment', body: 'Started with a 50-nucleotide sequence...', tag_names: []}. The backend processes the request and returns a 200 response. Kohl then refreshes the page (F5 or Cmd+R).

**Expected:**

After refresh, the page reloads and the editor fetches the saved note from GET /api/notes/{id}. The editor displays the same title and body that Kohl entered. localStorage is cleared (per the save success contract). The note persists in the database indefinitely — Kohl can close the browser, come back tomorrow, and the note is still there.

**Concern:**

If the schema migration did not run correctly, or if the id primary key is malformed, or if the title/body fields are not persisted correctly, Kohl's note will either not save at all (500 error, breakage) or will save but not restore on refresh (silent data loss, also breakage). This is the core user contract for Ticket 010: the schema must survive the save-and-reload cycle.

**Property:**

A note created and persisted via the schema contract is durable across page reloads and survives indefinitely in the database.

**Implies:**
- SQLite migration is applied and the notes table exists
- Note model can insert a row with title, body, created_at, updated_at
- The inserted row has a valid, unique id (primary key)
- Timestamps are set server-side (not by the client)
- GET /api/notes/{id} can retrieve the persisted row by its id
