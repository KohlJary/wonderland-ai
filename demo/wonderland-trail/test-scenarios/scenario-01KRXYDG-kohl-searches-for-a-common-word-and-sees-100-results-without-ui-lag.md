## Scenario 196: Kohl searches for a common word and sees 100+ results without UI lag

**GUID:** 01KRXYDGJMBMVN3X0NM5ETQ1NZ
**Severity:** degradation

**Setup:**

Kohl has 500 notes in the system. She searches for 'the' (a common word that appears in many titles and bodies).

**Trigger:**

The search returns 250 matching notes and displays the first page (20 results).

**Expected:**

The results list renders without visible lag or stuttering. Scrolling through the results list is smooth. Clicking 'Next' to go to page 2 takes ≤300ms to load and render.

**Concern:**

If the frontend naively renders all 250 results at once (instead of paginating), the page becomes sluggish or unresponsive. Kohl will perceive the app as broken even though the search logic is correct.

**Property:**

search-results-ui-must-handle-100+-results-gracefully-via-pagination-or-virtualization

**Implies:**
- frontend-must-implement-pagination-controls-or-virtual-scroll-to-avoid-rendering-all-results-at-once
