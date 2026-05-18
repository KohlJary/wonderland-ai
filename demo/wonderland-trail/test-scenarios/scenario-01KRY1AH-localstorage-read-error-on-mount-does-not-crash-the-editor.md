## Scenario 294: localStorage read error on mount does not crash the editor

**GUID:** 01KRY1AH3KPSQ1N168XD0XCQTX
**Severity:** breakage

**Setup:**

localStorage contains corrupted JSON in the 'editor_draft' key (e.g., '{title: broken').

**Trigger:**

Page loads; Editor mounts and tries to JSON.parse the corrupted value.

**Expected:**

Editor catches the parse error, logs it, and proceeds with empty state. User can still edit and save. No white screen of death.

**Concern:**

Current implementation has a try-catch around localStorage parsing, so this should be OK. But debounce-aware version must maintain that safety. If debounce implementation does not also wrap localStorage.setItem, a write error mid-burst will crash the editor (unacceptable).
