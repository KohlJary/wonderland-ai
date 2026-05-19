## Scenario 257: App boots with localStorage buffer, backend connection fails during reconciliation fetch

**GUID:** 01KRY19G98KE8SJKZ3Z7K85J7Z
**Severity:** degradation

**Setup:**

Kohl has unsaved text in localStorage (failed save, or keystroke buffer from a prior session). On reboot, the fetch to the backend times out or returns 5xx.

**Trigger:**

App attempts to boot, tries to fetch backend state for reconciliation, connection fails.

**Expected:**

App displays a 'offline' or 'retry' indicator, and makes the localStorage buffer available for editing (Kohl can keep working, resume saving when connection returns). App does NOT discard the localStorage buffer.

**Concern:**

The app might not have a fallback for offline boot. It might hang waiting for the backend, or worse, it might clear localStorage to 'clean state' and then fail to load anything, stranding Kohl with no access to her unsaved work.

**Property:**

If backend reconciliation fails, the app must preserve localStorage content and allow editing in a degraded mode (save will fail, but edit works).

**Implies:**
- Implies error handling and fallback UI. Flag for Tweedledee (frontend offline handling).
