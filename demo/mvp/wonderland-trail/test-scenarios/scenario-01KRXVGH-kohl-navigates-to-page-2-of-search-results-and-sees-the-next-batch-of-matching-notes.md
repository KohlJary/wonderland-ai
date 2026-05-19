## Scenario 089: Kohl navigates to page 2 of search results and sees the next batch of matching notes

**GUID:** 01KRXVGHT2Y73C5JV7SEK1JJ77
**Severity:** degradation

**Setup:**

Kohl searches for 'test' and gets 47 results, paginated 20 per page. She's on page 1 of 3. She clicks Next to see page 2.

**Trigger:**

Kohl clicks the 'Next' button (or page 2 link) while viewing search results.

**Expected:**

The page reloads/updates with results 21-40 of the 47 total. Pagination shows 'Page 2 of 3'. The Previous button is now clickable. If she clicks Next again, she sees results 41-47 on page 3.

**Concern:**

If pagination doesn't work, Kohl can only see the first 20 results and will assume notes on pages 2+ don't exist. If offset is miscalculated, she'll see duplicate results or gaps. Pagination is how she discovers work she forgot about.

**Property:**

Pagination offset and limit are applied correctly
