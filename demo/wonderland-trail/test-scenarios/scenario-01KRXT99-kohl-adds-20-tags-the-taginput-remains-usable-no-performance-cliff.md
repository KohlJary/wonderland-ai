## Scenario 017: Kohl adds 20+ tags — the TagInput remains usable (no performance cliff)

**GUID:** 01KRXT99M7QSR234FW4T0095TY
**Severity:** degradation

**Setup:**

Kohl has been tagging a complex experiment with many dimensions: 'temperature-20c', 'pressure-1atm', 'substrate-glass', 'catalyst-platinum', 'solvent-acetone', 'batch-001', 'run-A', 'replicate-yes', 'notes-anomaly-observed', 'method-heating', 'duration-2h', 'notes-cooling-phase', 'contamination-check-passed', 'qc-approved', 'archive-yes', 'project-crystal-growth', 'funder-nsf', 'deadline-2025-02-01', 'reviewer-alice', 'reviewer-bob'. The TagInput is visually displaying all 20 chips.

**Trigger:**

Kohl types tag number 21, 'final-notes', and presses Enter.

**Expected:**

The new chip appears without noticeable lag (< 200ms visual response). The input remains responsive. The chip list is scrollable if needed, or wraps naturally without overflow issues. Save button is still clickable.

**Concern:**

If the component bogs down with 20+ tags, rendering becomes sluggish, the input feels unresponsive, or chips overflow in ugly ways, Kohl's tagging experience degrades from snappy to laggy. For an experimental scientist with complex multi-dimensional work, 20+ tags per note is not unrealistic.

**Property:**

TagInput scales gracefully to moderate tag counts (20+)
