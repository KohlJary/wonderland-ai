## Scenario 012: Kohl removes a tag by clicking the X on a chip

**GUID:** 01KRXT99M7QSR234FW4T0095TS
**Severity:** breakage

**Setup:**

The editor has three tags already added as chips: 'experimental-setup', 'results-batch-2', 'pending-analysis'. Each chip has a visible X or close icon.

**Trigger:**

Kohl clicks the X on the 'results-batch-2' chip.

**Expected:**

The 'results-batch-2' chip disappears immediately. The remaining two chips ('experimental-setup', 'pending-analysis') stay in place. The tag list in memory is updated.

**Concern:**

If tag removal fails, Kohl is stuck with unwanted tags and cannot correct her input before saving.

**Property:**

Tag removal is immediate and non-blocking
