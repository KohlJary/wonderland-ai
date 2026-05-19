## Ruling 004: Multi-tab write collision must be detected and surfaced before silent overwrite

**GUID:** 01KRXRTQ5Q464N08HVEGQ3SYSP
**Severity:** high
**Domain:** data-handling
**Source:** ADR: Server-authoritative note persistence with client-side keystroke buffer; Alice's concern about silent data loss

**Citation:**

CWE-362 (Concurrent Modification Without Proper Synchronization); implicit contract in Kohl's mental model ('I can safely edit notes without worrying about accidental data loss')

**Finding:**

The ADR's single-user assumption is architectural (simplifies sync logic) but not behavioral (Kohl may open two tabs by accident). If two tabs edit the same note and both attempt to save, the second save overwrites the first without warning. The audit trail captures only the final saved state, not the intermediate edit, so recovery is not possible. Kohl loses work silently and has no visibility into why.

**Required Remediation:**

Before the first save from tab B overwrites tab A's unsaved work, the client must detect that tab A also has unsaved changes to the same note and surface this to Kohl with a clear choice (Keep tab A's version, Keep tab B's version, or Merge manually by editing in one tab and discarding the other). The detection must happen at sync time, not after overwrite.

**Acceptance Criteria:**
- Kohl opens note X in tab A, edits, leaves unsaved
- Kohl opens note X in tab B, edits, attempts to save
- Before tab B's save completes, Kohl is shown a collision warning naming both versions and asking which to keep
- Kohl's choice is respected; the unchosen version is displayed as 'discarded' so she can manually merge if needed
- Audit trail records both the collision event and Kohl's choice

**Residual Risk:**

If Kohl ignores the warning and clicks 'Keep this version' without reading, she may not realize she discarded work. Mitigation: make the UI explicit ('You will lose the edits from tab A') rather than abstract ('Choose version'). Residual risk is acceptable because the warning exists and Kohl has agency to recover from it.

**Compliance Implications:**

Single-user note-taking does not trigger GDPR or HIPAA, but the audit trail must record collision events for forensic clarity if Kohl later reports data loss. The trail should show 'Collision on 2024-01-15 14:32; user chose version from tab B' so that recovery is possible.

**Audit Reference:**

Audit trail entry: collision_event(note_id, timestamp, tab_A_last_saved, tab_B_last_saved, user_choice, final_saved_state)
