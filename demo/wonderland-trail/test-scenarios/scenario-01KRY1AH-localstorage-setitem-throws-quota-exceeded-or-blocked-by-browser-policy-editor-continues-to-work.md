## Scenario 295: localStorage.setItem throws (quota exceeded, or blocked by browser policy); editor continues to work

**GUID:** 01KRY1AH3KPSQ1N168XD0XCQTY
**Severity:** degradation

**Setup:**

localStorage is full (quota exceeded) or blocked by a browser security policy (e.g., sandboxed iframe, private browsing on some browsers).

**Trigger:**

User types 'hello'; debounce fires and tries to localStorage.setItem.

**Expected:**

setItem throws; editor catches the error, logs it, and allows the user to continue editing. Pressing Save still works (attempts to POST to backend, which is the source of truth). User sees optional warning ('unable to buffer to localStorage, but you can save to backend').

**Concern:**

Without error handling on setItem, the debounce handler will crash and stop all keystroke processing. Editor becomes unresponsive. Catastrophic.
