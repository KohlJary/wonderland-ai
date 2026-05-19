## Scenario 050: Kohl types a two-paragraph experimental note with title and reads it back after reload

**GUID:** 01KRXTBSX1SQXPMXS4J54GRZBM
**Severity:** silent-wrongness

**Setup:**

Kohl opens the editor. Title field is empty. Body field is empty. localStorage is empty.

**Trigger:**

Kohl types 'Rust async patterns' into title field, then tabs to body and types a 150-word paragraph about tokio spawn semantics, then another 100-word paragraph on task cancellation. She waits 1 second (past the keystroke debounce window) without typing more.

**Expected:**

Title field shows 'Rust async patterns'. Body field shows both paragraphs joined with newlines. localStorage contains a JSON object with {title: 'Rust async patterns', body: '...150-word paragraph...\n...100-word paragraph...'}. (Kohl doesn't need to see localStorage directly; she just needs to know it's there so she can recover it later.)

**Concern:**

If keystroke buffering is broken or debounce is too aggressive, Kohl's work could be lost to a stray browser crash. The localStorage buffer is her safety net; if it doesn't capture both title and body accurately, the feature fails silently — she won't know until she reloads.

**Property:**

keystroke buffer captures multi-field state with both title and body

**Implies:**
- user-types-a-note-title-and-body-keystroke-autosave-writes-both-to-localstorage-before-user-clicks-save
