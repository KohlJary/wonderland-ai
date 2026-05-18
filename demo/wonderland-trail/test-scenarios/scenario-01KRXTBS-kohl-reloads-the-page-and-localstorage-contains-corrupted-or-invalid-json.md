## Scenario 055: Kohl reloads the page and localStorage contains corrupted or invalid JSON

**GUID:** 01KRXTBSX1SQXPMXS4J54GRZBS
**Severity:** degradation

**Setup:**

Kohl has previously saved a draft. localStorage contains a key 'editor_draft' with a malformed JSON value: '{title: "broken", body: [unclosed array}'. The editor component is about to mount and attempt to restore.

**Trigger:**

The editor mounts and tries to parse localStorage['editor_draft']. JSON.parse() fails because the stored value is not valid JSON.

**Expected:**

The editor catches the parse error, logs it (optionally), and starts with blank fields. No crash. No error displayed to Kohl (or a soft message: 'Draft recovery failed; starting fresh'). The Save button is ready for her to type a new note.

**Concern:**

If the editor doesn't handle JSON parse errors, it crashes on mount. Kohl reloads and sees a blank or error screen. She can't use the editor until she manually clears localStorage (which she won't know to do). This is a hard failure that blocks the feature.

**Property:**

editor handles localStorage parsing failures gracefully

**Implies:**
- localstorage-is-empty-or-contains-invalid-json-editor-starts-with-blank-fields-graceful-degradation
