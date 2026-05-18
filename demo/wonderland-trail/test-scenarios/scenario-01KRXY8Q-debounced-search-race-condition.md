## Scenario 181: Debounced search triggers race condition when user changes query before debounce completes

**GUID:** 01KRXY8Q (assigned)
**Severity:** degradation

**Setup:**

Search.tsx has results displayed from a previous query. User types a new query character-by-character rapidly.

**Trigger:**

User types 'transformer' very quickly (keystroke every 80ms), triggering 11 keystrokes in 880ms. Debounce is 300ms. At t=380ms, first debounce fires and fetches results for 't'. At t=480ms (keystroke 6), the debounce timer restarts. At t=780ms, second debounce fires and fetches 'transfor'. At t=880ms (keystroke 11), first API response arrives with results for 't'. At t=1080ms, second API response arrives with results for 'transfor'. The final rendered results should be 'transformer' (page 1 of many), but due to async timing, the stale 'transfor' results might overwrite the final 'transformer' results.

**Expected:**

The final displayed results match the final query ('transformer'), not an intermediate one ('t' or 'transfor'). The UI shows results for the query the user typed last.

**Concern:**

The Search.tsx component doesn't handle out-of-order API responses. If request B is issued after request A, but response A arrives after response B, request A's results will be displayed even though they're stale. This is a classic race condition in debounced search. The implementation uses a single `results` state with no request ID, abort controller, or ordering mechanism to discard stale responses.

**Property:**

When the user issues multiple search queries in rapid succession, the displayed results correspond to the final query, never to an intermediate query, regardless of API response order.

**Implies:**

- Implies potential race condition in Tweedledee's implementation. May require request ID/abort controller to cancel inflight requests when a new query is issued.
