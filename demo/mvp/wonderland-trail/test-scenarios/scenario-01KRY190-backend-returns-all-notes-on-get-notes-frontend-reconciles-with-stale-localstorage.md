## Scenario 246: Backend returns all notes on GET /notes, frontend reconciles with stale localStorage

**GUID:** 01KRY190Z3094B2DF4C3RP2H58
**Severity:** degradation

**Setup:**

Kohl opens the app. localStorage contains a draft note (title='Draft', body='draft body', updated_at=T1). Backend has three persisted notes (updated_at=T0 < T1 < T2).

**Trigger:**

Frontend calls GET /notes on boot and receives the three persisted notes. Frontend merge logic must decide which draft to keep.

**Expected:**

GET /notes returns all three persisted notes in reverse chronological order (T2, T1, T0). Frontend detects that the localStorage draft has an intermediate timestamp (T1) and either (a) merges the localStorage draft as a new note, (b) merges it into the T1 note if revision_id matches, or (c) flags it as a conflict.

**Concern:**

The contract says GET /notes returns all notes, but doesn't specify the merge strategy. If the frontend doesn't have a clear recipe for reconciliation, users could lose buffered work. The endpoint itself is correct; the concern is whether the frontend has the information it needs.

**Property:**

For all notes persisted since the last localStorage save, GET /notes must return them, and the frontend merge logic must be able to order them by timestamp and detect which one corresponds to the stale draft.

**Implies:**
- Implies frontend reconciliation strategy is specified somewhere — flag for Alice or Tweedledee.
