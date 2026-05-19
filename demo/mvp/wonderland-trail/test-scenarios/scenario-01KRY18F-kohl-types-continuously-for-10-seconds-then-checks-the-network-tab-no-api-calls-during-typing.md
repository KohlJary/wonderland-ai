## Scenario 243: Kohl types continuously for 10 seconds, then checks the network tab — no API calls during typing

**GUID:** 01KRY18F88GKW92A57SY2C1JVN
**Severity:** silent-wrongness

**Setup:**

Kohl has the note editor open with empty state. Developer tools (network tab) are visible in her setup for inspection.

**Trigger:**

Kohl types steadily for 10 seconds: 'Here is my hypothesis about...' (adding words one by one, normal typing speed, ~60 words total).

**Expected:**

The network tab shows zero API calls during those 10 seconds. localStorage is being hit (can be verified via DevTools Storage tab), but not the backend. The save endpoint is not called until she explicitly clicks 'Save' or until a 'save on blur' trigger fires (if implemented).

**Concern:**

If every keystroke fires a backend save, the server gets hammered and Kohl's typing feels sluggish. The debounce + localStorage design exists to avoid this. Silent wrongness: the UI feels responsive but the backend is actually drowning.

**Property:**

debounce prevents keystroke-level backend calls
