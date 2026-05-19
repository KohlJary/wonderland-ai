## Scenario 362: Kohl sees collision warning and chooses to load the server version; her draft is discarded safely

**GUID:** 01KRY1F5JJWC63TXB9SQCCBZWH
**Severity:** degradation

**Setup:**

Tab B has just received a 409 Conflict response from the Save attempt. The collision warning modal is displayed, showing Tab B's draft vs. the server's version (which includes Tab A's change).

**Trigger:**

Kohl reads the modal and realizes Tab A made a change she wants to keep. She clicks 'Load Server Version' button in the modal.

**Expected:**

The editor is reset to the server state (received in the 409 response body). The body text changes to reflect Tab A's edit. The revision_id is updated to the new server revision. The keystroke buffer in localStorage is cleared (since the user chose to abandon the draft). The collision warning closes. The note now shows the merged state from Tab A.

**Concern:**

If the collision warning is not shown, or if the 'Load Server Version' action doesn't reset the editor properly, Kohl might attempt to save again and get stuck in a retry loop, or she might lose track of what state the editor is in. Degradation because it's not a complete loss of work (the warning and choice mechanism exist), but the UX is confused if the recovery flow is broken.

**Property:**

collision warning resolution flow allows safe recovery
