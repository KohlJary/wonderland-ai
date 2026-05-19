## Scenario 334: If-Match validation catches multi-tab collision: Tab A saves, Tab B's stale If-Match is rejected with 409

**GUID:** 01KRY1DJHRX8TH9EM6XEXWJ9BB
**Severity:** breakage

**Setup:**

Tab A and Tab B both GET /notes/42 at time T0, receive revision_id='hash_old'. Tab A edits title, saves at T1 with If-Match: hash_old (succeeds, server now has revision_id='hash_new'). Tab B is still editing.

**Trigger:**

Tab B saves at T2 with PUT /notes/42 and header If-Match: hash_old.

**Expected:**

Backend detects mismatch (server's current revision_id='hash_new' != If-Match header 'hash_old'). Returns 409 Conflict with {error: 'ConflictError', server_revision_id: 'hash_new', server_state: {...}}. Note is NOT modified.

**Concern:**

If backend does not validate If-Match or validates but proceeds with the save anyway, Tab B silently overwrites Tab A's edits. Kohl loses work without warning. Silent-wrongness.

**Property:**

If save_A completes with If-Match=R_old producing revision_id=R_new, and then save_B is attempted with If-Match=R_old, the system MUST reject save_B (return 409) when R_old != R_new.

**Implies:**
- Implies architecture: PUT endpoint must validate If-Match before applying changes. Validation must be atomic with the write.
- Implies API contract: If-Match header must be required on PUT. Missing If-Match should be an error (400 or auto-fail with 409).
