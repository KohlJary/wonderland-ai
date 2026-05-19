## Scenario 104: Performance: Kohl has 1000 notes; she types a search term that matches 500 notes. Does the UI lag?

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY4A
**Severity:** degradation

**Setup:**

App has 1000 notes. Kohl types a common search term.

**Trigger:**

Results list updates to show 500 matching notes.

**Expected:**

The UI remains responsive. No perceptible jank or lag.

**Concern:**

If filtering is client-side (per story's 'instant'), the browser has to iterate over 1000 notes and filter on each keystroke. On a slow device, this might lag. If filtering is server-side (per tickets), the network latency might be > 100ms. Either way, performance matters for the 'instant' promise.

**Property:**

For all note lists up to a reasonable size (1000+ notes), search updates remain responsive (< 100ms perceived latency).

**Implies:**
- Implies performance budget and architecture decision (client vs server filtering) — flag for Cat.
