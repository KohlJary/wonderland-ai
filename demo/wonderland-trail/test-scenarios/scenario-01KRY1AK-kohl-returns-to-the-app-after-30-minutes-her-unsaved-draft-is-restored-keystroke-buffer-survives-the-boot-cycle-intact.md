## Scenario 296: Kohl returns to the app after 30 minutes: her unsaved draft is restored, keystroke buffer survives the boot cycle intact

**GUID:** 01KRY1AKDJCTY1526GW9Z2EK9K
**Severity:** silent-wrongness

**Setup:**

Kohl has been editing a note for 5 minutes. Title is 'Experiment Log', body is '## Day 5

Observations: membrane integrity...'. She has NOT clicked Save. localStorage holds {title: 'Experiment Log', body: '## Day 5

Observations: membrane integrity...', tags: [], lastSyncedAt: null (never saved)}. Backend has no record of this note (POST /notes was never called). Kohl steps away. 30 minutes pass. Browser is still open, but the component has unmounted and remounted (page refresh, or navigation away and back to the app).

**Trigger:**

Kohl returns to her desk. The app is still open. The editor component mounts. Editor.useEffect runs and checks localStorage for a buffered draft.

**Expected:**

The editor populates with the exact title and body from localStorage. The editor shows 'New Note' (unsaved state). Save button is enabled. The unsaved keystroke buffer is ready for Kohl to continue editing or discard.

**Concern:**

If the boot reconciliation logic clears localStorage before checking it, or if it tries to fetch GET /notes/{id} without an id (the note was never saved, so no id exists), Kohl's 30-minute draft vanishes. This is silent data loss — the app boots, Kohl sees a blank editor, and doesn't realize she lost work.

**Property:**

localStorage keystroke buffer survives across page reload/remount when the note has never been saved.

**Implies:**
- app-boots-and-immediately-tries-to-fetch-note-but-noteId-is-null-should-load-from-localStorage-not-crash
- unsaved-keystroke-buffer-persists-across-browser-navigation-and-component-remount
