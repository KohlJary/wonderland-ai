## Scenario 195: Kohl navigates between pages of search results and the page count updates correctly

**GUID:** 01KRXYDGJMBMVN3X0NM5ETQ1NY
**Severity:** silent-wrongness

**Setup:**

Kohl searched for 'note' and got 47 results (showing 20 per page, page 1 of 3). She is viewing the first page.

**Trigger:**

Kohl clicks the 'Next' button at the bottom of the results list.

**Expected:**

The page advances to page 2. The results list now shows results 21–40. The pagination info reads 'Page 2 of 3' or 'Results 21–40 of 47'. The 'Previous' button becomes clickable. The 'Next' button remains clickable.

**Concern:**

If pagination doesn't work, Kohl is trapped on page 1 and cannot see all her results. If the page count is wrong, she may think she's seen all results when she hasn't.

**Property:**

pagination-must-correctly-calculate-total-pages-and-navigate-between-them
