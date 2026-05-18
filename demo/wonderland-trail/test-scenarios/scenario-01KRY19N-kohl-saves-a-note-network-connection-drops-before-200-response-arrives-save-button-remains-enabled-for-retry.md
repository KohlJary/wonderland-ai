## Scenario 259: Kohl saves a note, network connection drops before 200 response arrives, Save button remains enabled for retry

**GUID:** 01KRY19NJ0GS53FVHNDWBCBT8A
**Severity:** breakage

**Setup:**

Kohl is editing a note in the editor. The keystroke buffer has {title: 'Experiment v2', body: 'Initial findings...', tags: ['rust', 'async']}. The app has a valid revision_id from the last load (e.g., 'rev_1'). Kohl clicks Save.

**Trigger:**

The fetch() call to PUT /notes/{id} starts. After the request is sent, the network connection is severed (Network tab throttle or offline mode).

**Expected:**

The frontend detects the network error (timeout or 'no network' error from fetch). The Save button remains visible and enabled. An error message is shown to Kohl. The keystroke buffer in localStorage is NOT cleared, so if she reloads the page or retries Save after network is restored, her edits are still there.

**Concern:**

If the Save button is disabled on error, Kohl cannot retry. If the error is swallowed silently (no message), Kohl thinks the save succeeded when it didn't. If localStorage is cleared anyway, her edits are lost even though no confirmation was received from the server.

**Property:**

For all network failures (connection loss, timeout, DNS failure), the frontend must (a) show an error message to Kohl, (b) leave Save button enabled, (c) preserve the keystroke buffer so retry is possible.

**Implies:**
- Implies error handling UI design—the error message must be clear that the save failed and retry is possible.
