## Scenario 286: Kohl's app is offline; she clicks Save; keystroke buffer is preserved; Save button shows error; work is safe

**GUID:** 01KRY1A1CJG4S1VG4H5J0GAQC1
**Severity:** degradation

**Setup:**

Kohl's browser loses network connectivity (airplane mode, network cable unplugged). She has been editing a note offline (localStorage has the keystroke buffer). She clicks the Save button, unaware that the network is down.

**Trigger:**

Editor calls updateNote(noteId, {...payload}), which calls fetch() to PATCH /api/notes/{noteId}. Network is down; fetch times out after 30s or fails immediately with network error.

**Expected:**

fetch() rejects with a network error (not a 2xx or 4xx/5xx response — no response at all). Editor's error handler catches the error and displays 'Save failed: network connection lost. Your work is safe in the browser. Try again when network is available.' Save button re-enables. localStorage keystroke buffer is NOT cleared (only cleared on 200 response). Kohl can retry manually once network returns, and her unsaved edits are still there.

**Concern:**

If the frontend clears localStorage on network error (treating it like a successful save), Kohl loses her work when she thought she saved. If the frontend doesn't show an error message, Kohl doesn't know the save failed and assumes her work is on the server. If the Save button stays disabled after failure, Kohl is stuck. Silent data loss or user confusion is the failure mode.

**Property:**

offline_save_failure_preserves_keystroke_buffer_and_allows_retry
