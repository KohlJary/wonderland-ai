## Scenario 291: User types in title field; body field is not touched; localStorage updates reflect title-only changes

**GUID:** 01KRY1AH3KPSQ1N168XD0XCQTT
**Severity:** degradation

**Setup:**

Editor mounted with {title: '', body: 'existing body', tags: []}.

**Trigger:**

User types 'my title' in title input (7 keystrokes).

**Expected:**

Each keystroke in title field increments title length; after 300ms debounce closes, localStorage is written once with {title: 'my title', body: 'existing body', tags: []}. Body field is not touched; localStorage reflects the combined state, not just the changed field.

**Concern:**

Without debounce, each title keystroke writes separately. With debounce, a burst of title edits counts as a single logical edit. The localStorage entry is always the full editor state (both title and body), not field-level deltas.
