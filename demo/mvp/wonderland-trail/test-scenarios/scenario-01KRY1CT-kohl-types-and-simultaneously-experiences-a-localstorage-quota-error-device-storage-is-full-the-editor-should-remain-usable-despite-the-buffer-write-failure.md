## Scenario 321: Kohl types and simultaneously experiences a localStorage quota error (device storage is full)—the editor should remain usable despite the buffer write failure

**GUID:** 01KRY1CT0KYYZH13BXHBA5K1JP
**Severity:** degradation

**Setup:**

Kohl's device has limited storage. localStorage is near capacity. The editor mounts and initializes the keystroke handler.

**Trigger:**

Kohl types 'This is a long experimental report with detailed measurements and analysis' (70 characters). The keystroke handler attempts to write to localStorage, but localStorage.setItem throws a QuotaExceededError.

**Expected:**

The setItem error is caught and logged (or silently ignored per the component's error handling). The editor remains responsive; the user can continue typing and clicking Save without crashes. When Save is clicked, the editor sends the current in-memory state to the backend. The lack of a buffer is a degradation (no recovery on reload), not a blocker.

**Concern:**

If the keystroke handler throws an uncaught error on QuotaExceededError, the component crashes and Kohl cannot interact with the editor. This is a blocking failure. The handler must gracefully degrade.

**Property:**

localStorage write errors do not crash the editor; typing and saving continue despite quota or access issues.
