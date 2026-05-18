## Scenario 258: App boots while a prior save request is still in flight — no merge collision

**GUID:** 01KRY19G98KE8SJKZ3Z7K85J80
**Severity:** breakage

**Setup:**

Kohl clicks save (a POST request goes to the backend). Before the response arrives, she closes the tab. On reopen, the save response never arrives, but the backend has already recorded the save (revision ID 6). localStorage still has the pre-save or mid-save buffer.

**Trigger:**

App boots. Frontend initiates reconciliation fetch while the prior save's response is still pending (or already completed but the client doesn't know).

**Expected:**

Backend returns revision 6 (the completed save). Frontend sees that backend is newer than localStorage, shows revision 6 content, clears localStorage. No duplicate save, no lost content.

**Concern:**

This is the collision case. The app might not detect that a save was in-flight and might attempt to reapply the localStorage state, creating a duplicate save or overwriting the backend state. Or it might get into a state where localStorage and backend both exist but neither is marked as current.

**Property:**

The app must detect whether an in-flight save request succeeded on the backend (by comparing revision IDs), and if so, treat the backend as the source of truth.

**Implies:**
- Implies the backend save endpoint must be idempotent or return a revision ID that the frontend can use to detect success. Flag for Tweedledum (backend save contract).
