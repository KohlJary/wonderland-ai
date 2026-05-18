## Scenario 289: User types, then stops; localStorage persists the final state exactly once after 300ms debounce window closes

**GUID:** 01KRY1AH3KPSQ1N168XD0XCQTR
**Severity:** degradation

**Setup:**

Editor mounted with empty state.

**Trigger:**

User types 'hello world' (12 keystrokes over ~600ms real time, e.g., 50ms between keystrokes), then stops for 1 second.

**Expected:**

After first keystroke, a debounce timer starts. Keystrokes during the 300ms window reset the timer. After the user stops typing and 300ms elapses, localStorage is written exactly once with {title: '', body: 'hello world', tags: []}.

**Concern:**

Without debounce, Editor writes {'body': 'h'} on keystroke 1, {'body': 'he'} on keystroke 2, etc., creating a chatty localStorage trail. With debounce, the final state is written once after typing stops. This reduces I/O and also ensures localStorage always reflects a coherent editor state at predictable moments.
