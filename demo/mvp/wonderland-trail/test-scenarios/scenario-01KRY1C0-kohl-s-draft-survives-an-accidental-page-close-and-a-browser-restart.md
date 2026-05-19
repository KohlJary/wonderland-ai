## Scenario 312: Kohl's draft survives an accidental page close and a browser restart

**GUID:** 01KRY1C0REHH0KMQPVA6ED258G
**Severity:** degradation

**Setup:**

Kohl writes 1000 words in the editor (keystroke buffer writes to localStorage on every keystroke). She hasn't clicked Save yet. Phone dies; browser process terminates. Six hours later, she powers on the phone and opens the app again.

**Trigger:**

App mounts after browser restart. loadNotes() queries the backend. localStorage still contains the draft (browser data persists across restart on most platforms). GET /notes returns the list of previously-saved notes (not including the unsaved draft, which has no id).

**Expected:**

Editor initializes with the 1000-word draft restored from localStorage. Kohl sees her work intact and can immediately click Save. The UI shows 'Unsaved changes' or similar feedback indicating the draft hasn't been persisted yet.

**Concern:**

If localStorage is cleared during app initialization (e.g., for 'cleaning up'), Kohl's draft is lost permanently. The keystroke buffer's entire purpose is to protect against this scenario (browser crash, power loss, accidental close). Loss would be silent — Kohl would see a blank editor and have to retype or give up.

**Property:**

localStorage survives app restarts and is treated as the source of truth for unsaved work.

**Implies:**
- localStorage is NOT cleared on app mount; it's only cleared after successful save (200 response)
- Editor component restores from localStorage in useEffect, with error handling if JSON parsing fails
