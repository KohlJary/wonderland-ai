## Scenario 253: App boots with newer localStorage buffer than backend-saved version — buffer is preserved

**GUID:** 01KRY19G98KE8SJKZ3Z7K85J7V
**Severity:** silent-wrongness

**Setup:**

Kohl writes 'First draft of attention analysis' to a note, the buffer writes to localStorage but before a save button is clicked, she closes the tab. The backend has an older version: 'First draft' (saved from 20 minutes ago). On reopen, localStorage has the fuller text.

**Trigger:**

App boots. Frontend fetches the backend version and the localStorage buffer. Both exist, backend timestamp is older than localStorage modification time.

**Expected:**

Frontend displays the localStorage buffer content, and flags it as 'unsaved changes' or surfaces a save button. The newer, longer text is visible. When Kohl saves, it persists to backend.

**Concern:**

The app might show the backend version (silently discarding the localStorage buffer), or it might show the buffer but then overwrite it with the backend version after a moment, creating a flash-of-wrong-content bug that only some users see depending on timing. This is the classic 'which write wins' failure.

**Property:**

For all (localStorage_content, backend_content) pairs where both are valid and have modification timestamps, the app must display the content with the later timestamp, or explicitly ask the user which to keep.

**Implies:**
- Implies the frontend load controller must timestamp both sources and compare. Flag for Tweedledum (backend load endpoint) and Tweedledee (frontend boot flow).
