## Scenario 223: Kohl types very fast ('experiment' in 0.3s), debounce fires 2-3 requests in flight simultaneously — UI shows correct results from the last one

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HXC
**Severity:** silent-wrongness

**Setup:**

Kohl types 'e', then 'x', then 'pe', then 'rim', then 'ent' — very quickly, faster than the 300ms debounce. 2–3 debounced requests may fire to the backend before the final one completes.

**Trigger:**

Multiple API requests are in flight (for 'expe' and 'experiment'). Responses may arrive out of order.

**Expected:**

The UI displays the results for 'experiment' (the final, complete query), not the results for 'expe' (a prior, incomplete query). The result count and highlighted terms reflect the correct, final search. No stale results are shown.

**Concern:**

If responses arrive out of order and the UI renders the earlier result, Kohl sees wrong matches and confusing highlights. The query input says 'experiment' but results show matches for 'expe'.

**Property:**

Out-of-order network responses must not overwrite newer results with stale data.

**Implies:**
- request-sequencing-via-abort-or-generation-id
- no-stale-result-rendering
- final-query-state-matches-displayed-results
