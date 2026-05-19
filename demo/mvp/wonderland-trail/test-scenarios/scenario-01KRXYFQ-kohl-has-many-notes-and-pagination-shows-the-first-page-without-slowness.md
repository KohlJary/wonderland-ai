## Scenario 233: Kohl has many notes and pagination shows the first page without slowness

**GUID:** 01KRXYFQH721FMRYBB1WJJ1A0K
**Severity:** degradation

**Setup:**

Kohl has 200 notes. She opens search and submits a broad query that matches 50 notes.

**Trigger:**

Search results load and display the first page (20 results per page, per contract-note-008).

**Expected:**

Results appear within 500ms. Pagination controls show 'Page 1 of 3' or similar, with Next button available. The first 20 results are visible.

**Concern:**

If search on 200+ notes is slow, Kohl perceives the feature as broken or unresponsive. This impacts her workflow—she stops using search if it's sluggish.

**Property:**

Search on 200+ notes returns paginated results (first page) within 500ms on typical hardware.

**Implies:**
- performance-acceptance
