## Scenario 063: Kohl creates a new note, saves it, and sees her title and body persisted exactly as typed

**GUID:** 01KRXTE35W88GEZR30A8W5VQ4B
**Severity:** silent-wrongness

**Setup:**

Browser is open to the editor; localStorage is empty; no notes exist on the server

**Trigger:**

Kohl types 'Rust async patterns' in the title field, types 'Tokio task spawning behaves like...' in the body, clicks Save

**Expected:**

The Save button transitions to a success state (or briefly shows 'Saved'). The editor clears or shows the persisted note. When Kohl reloads the page, the title and body are exactly as she typed them, and localStorage is cleared

**Concern:**

If the server persists the wrong title, body, or timestamp, Kohl won't notice until she tries to retrieve the note later. This is data corruption that looks like success

**Property:**

Server persists title and body atomically with correct timestamps

**Implies:**
- POST /api/notes request body matches contract (title, body, tag_names)
- Response includes server-assigned id and ISO8601 timestamps
- localStorage is cleared after 200 response
