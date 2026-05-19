## Ruling 005: Multi-tab detection and warning must prevent silent overwrites

**GUID:** 01KRXRVRV3DW29H0F7KDZVGVWR
**Severity:** critical
**Domain:** data-handling
**Source:** adr slug=server-authoritative-note-persistence-with-keystroke-level-localstorage-buffer

**Citation:**

CWE-362 (Concurrent Modification Without Proper Synchronization); Alice's concern that multi-tab overwrites are silent data loss without visibility; ACID principle (Consistency) that a write operation must not lose prior writes without user awareness.

**Finding:**

The single-user assumption in the ADR does not prevent Kohl from opening two editor tabs by accident. If tab A has unsaved edits and tab B syncs to the backend, tab B's Save will overwrite tab A's work without warning. The audit trail captures only the final (tab B) state. Kohl experiences data loss without any indication it occurred.

**Required Remediation:**

Before a Save from the client is allowed to proceed, the frontend must detect whether the same note is currently open in another tab. If a collision is detected, the Save must be blocked and Kohl must be shown a warning naming which tab holds the competing edit. Kohl chooses which version to keep or manually merges. Collision detection must use localStorage as the coordination mechanism (the only shared client-side store across tabs).

**Acceptance Criteria:**
- Frontend code implements a tab-coordination protocol using localStorage (e.g., writing tab ID + timestamp to a 'note_X_editing' key; checking for competing keys before Save)
- When a collision is detected, the Save is blocked and a modal or banner appears naming 'This note is open in another tab' and offering 'Keep local edits', 'Discard and reload from server', or 'Merge manually'
- Test scenarios from Mad Hatter verify: (1) same note open in two tabs, one saves successfully; (2) second tab attempts save and collision is detected; (3) collision warning appears and blocks save until Kohl chooses a resolution
- Dormouse observability captures 'tab_collision_detected' events so we know if Kohl's actual behavior contradicts the single-user assumption

**Residual Risk:**

A user could close the collision warning and open the browser console to force a save, bypassing the guard. This is acceptable because it requires intentional circumvention; the guard protects against accidental overwrites, which is the common case.

**Compliance Implications:**

No specific compliance framework governs single-user note-taking applications; this ruling is grounded in data-integrity principle (ACID Consistency), not regulatory requirement.

**Audit Reference:**

Audit trail entry for each Save must include 'collision_check_passed' or 'collision_check_warned' field so that any save following a collision warning is visible as a deliberate choice, not a silent overwrite.
