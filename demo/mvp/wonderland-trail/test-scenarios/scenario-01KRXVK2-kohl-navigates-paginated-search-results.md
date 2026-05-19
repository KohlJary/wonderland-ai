## Scenario 110: Kohl navigates paginated search results

**GUID:** 01KRXVK28H5RPDTG82TGG11W9T
**Severity:** degradation

**Setup:**

Kohl's search term matches 45 notes. The results display as a paginated list (20 per page), with Prev/Next buttons and a page indicator ('Page 1 of 3').

**Trigger:**

Kohl is on page 1. She clicks the Next button to view notes 21–40.

**Expected:**

The results list updates to show notes 21–40. The page indicator shows 'Page 2 of 3'. The Prev button is now clickable (previously disabled). The Next button remains enabled. She can click Prev to go back to page 1.

**Concern:**

Without pagination, a search matching 500+ notes would render a single massive list, causing UI lag and overwhelming Kohl. Pagination keeps the interaction responsive.

**Property:**

pagination navigation
