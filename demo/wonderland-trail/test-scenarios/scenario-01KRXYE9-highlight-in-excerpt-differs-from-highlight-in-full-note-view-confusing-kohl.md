## Scenario 204: Highlight in excerpt differs from highlight in full note view, confusing Kohl

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHJ
**Severity:** degradation

**Setup:**

Search result shows a note with the phrase 'gradient scaling' highlighted in the excerpt. Kohl clicks to open the full note. The full note view renders the body and should highlight the same phrase.

**Trigger:**

Kohl clicks a search result. The note opens in EditorLayout or a read-only view.

**Expected:**

The phrase 'gradient scaling' remains highlighted in the full note view (if highlighting persists) or Kohl sees the exact match in context.

**Concern:**

If the search result highlights using substring matching (e.g., case-insensitive indexOf), but the full note view does not apply the same highlighting, Kohl is confused: 'I saw it highlighted in the results, why isn't it highlighted here?' Additionally, if the query string is not passed to the full-note view, the highlighting logic cannot re-apply the match.

**Property:**

For all search queries Q and matching notes N, if the search results highlight the match, opening the full note either (a) preserves the highlight (requires passing query context), or (b) clearly shows the match in context without highlighting (acceptable if the full view is read-only and previewing the match is enough).

**Implies:**
- Implies contract question: should the full-note view accept a query parameter to re-highlight the match? Or should search highlighting be transient (visible only in results list)? Flag for Cat to decide the contract.
