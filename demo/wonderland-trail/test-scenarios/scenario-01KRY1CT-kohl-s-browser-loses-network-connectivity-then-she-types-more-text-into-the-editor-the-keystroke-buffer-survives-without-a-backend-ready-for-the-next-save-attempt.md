## Scenario 319: Kohl's browser loses network connectivity, then she types more text into the editor—the keystroke buffer survives without a backend, ready for the next Save attempt

**GUID:** 01KRY1CT0KYYZH13BXHBA5K1JM
**Severity:** degradation

**Setup:**

Kohl has a saved note on the server. Her browser is briefly offline (no network). The editor is still open.

**Trigger:**

While offline, Kohl types 'New observation: the temperature sensor reading drifted' (50 characters) into the body.

**Expected:**

The keystroke buffer correctly writes to localStorage (network status is irrelevant for local storage). After 300ms of typing idle, localStorage['noteBuffer'] contains the new text. When network is restored and Kohl clicks Save, the editor sends the buffered content to the server.

**Concern:**

If the keystroke buffer somehow depends on or checks network status before writing, offline typing could be lost. The buffer should be resilient to network state changes.

**Property:**

Keystroke buffer writes to localStorage regardless of network availability; network state does not block buffer persistence.
