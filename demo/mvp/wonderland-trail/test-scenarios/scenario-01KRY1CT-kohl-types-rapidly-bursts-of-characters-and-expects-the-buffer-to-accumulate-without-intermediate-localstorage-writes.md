## Scenario 315: Kohl types rapidly (bursts of characters) and expects the buffer to accumulate without intermediate localStorage writes

**GUID:** 01KRY1CT0KYYZH13BXHBA5K1JG
**Severity:** degradation

**Setup:**

Kohl opens the editor and begins typing a longer note. The debounce timer is armed on the first keystroke.

**Trigger:**

Kohl types 200 characters continuously over ~10 seconds (bursts of 10-20 chars per second), then stops typing.

**Expected:**

During the typing burst, localStorage is not written on every keystroke. The debounce timer resets with each keystroke. Once Kohl stops (no keystroke for 300ms), localStorage['noteBuffer'] is updated once with the full 200-character text. localStorage is written exactly once, not 200 times.

**Concern:**

If the debounce resets every keystroke but still fires on keystroke N, the buffer thrashes the disk (performance degradation on slower devices). If the debounce does not reset, early saves might capture an incomplete draft. Kohl expects the buffer to capture her final intent, not intermediate states.

**Property:**

Debounce timer resets on every keystroke; only the final buffer state (after 300ms idle) is persisted.
