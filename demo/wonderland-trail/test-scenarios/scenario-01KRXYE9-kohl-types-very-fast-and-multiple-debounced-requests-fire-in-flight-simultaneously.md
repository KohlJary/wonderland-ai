## Scenario 208: Kohl types very fast and multiple debounced requests fire in flight simultaneously

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHP
**Severity:** silent-wrongness

**Setup:**

Kohl types 'transformer architecture attention' quickly (3 words in 2 seconds). Debounce is set to 300ms. Three requests fire: q=transformer, q=transformer+architecture, q=transformer+architecture+attention. Network latency is variable (100ms, 300ms, 200ms respectively). Responses arrive out of order: response 3 (300ms) arrives first, then response 1 (100ms), then response 2 (200ms).

**Trigger:**

Each response updates the search results. The last response to arrive becomes the displayed state.

**Expected:**

The final displayed results are for the most recent query ('transformer architecture attention').

**Concern:**

If responses are not tracked by request timestamp or query ID, the final state might be from an older query. Kohl typed 'transformer architecture attention' but sees results for 'transformer' (response 1, which arrived last chronologically but was the first query). This is silent wrongness: the results look plausible, but don't match the current input.

**Property:**

For all sequences of rapid queries with variable latency, the final displayed results correspond to the most recent query typed by the user, not the most recent response received.

**Implies:**
- Implies frontend concern: Use request abort (AbortController) or track query timestamps. When a new request fires, cancel any in-flight requests for older queries. Or, track the query string in state and ignore responses that don't match the current query.
