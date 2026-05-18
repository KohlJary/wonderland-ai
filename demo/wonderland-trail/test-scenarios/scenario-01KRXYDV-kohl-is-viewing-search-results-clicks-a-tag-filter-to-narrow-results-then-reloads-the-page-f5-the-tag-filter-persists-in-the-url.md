## Scenario 198: Kohl is viewing search results, clicks a tag filter to narrow results, then reloads the page (F5) — the tag filter persists in the URL

**GUID:** 01KRXYDVNXZN8XM83A00MPY61A
**Severity:** silent-wrongness

**Setup:**

Kohl is on /search?q=rust with 10 results displayed, and she can see tag suggestion buttons below the results

**Trigger:**

Kohl clicks the 'performance' tag suggestion button to filter results. The search re-runs and returns only notes with title/body matching 'rust' AND tagged with 'performance'. Kohl then presses F5 to reload the page

**Expected:**

After reload, the page loads with the same search query 'rust' and tag filter 'performance' applied. The search input shows 'rust', the 'performance' tag is shown as selected/active (visually distinct from unselected tags), and the results still show only notes matching both criteria

**Concern:**

If tag filters are stored in client-side component state rather than URL params, the reload will clear the filter. Kohl will see all 'rust' results again, not just the 'performance'-tagged subset. This is silent wrongness: the page appears to load, but the filter silently vanished. Kohl may think she lost the filter or that the search is broken

**Property:**

tag filters are URL-serialized and survive page reload
