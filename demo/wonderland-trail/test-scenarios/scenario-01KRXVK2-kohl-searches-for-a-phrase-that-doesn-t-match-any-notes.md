## Scenario 111: Kohl searches for a phrase that doesn't match any notes

**GUID:** 01KRXVK28H5RPDTG82TGG11W9V
**Severity:** silent-wrongness

**Setup:**

Kohl has notes about attention, transformers, and deep learning. She opens search.

**Trigger:**

Kohl types 'quantum computing' (a phrase not in any of her notes).

**Expected:**

The search results pane displays 'No results found' or 'No notes match your search' with an empty list. The input remains visible, so Kohl can try a different search term. No error message or crash.

**Concern:**

If the zero-results case is not handled, Kohl might think the search is broken or slow (still loading). Explicit zero-results messaging is necessary so she knows to try a different query, not just wait.

**Property:**

zero-results handling
