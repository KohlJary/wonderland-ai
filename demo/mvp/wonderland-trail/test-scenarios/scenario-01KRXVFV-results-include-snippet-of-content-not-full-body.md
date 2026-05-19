## Scenario 081: Results include snippet of content (not full body)

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9N
**Severity:** degradation

**Setup:**

Note with title='title', body='This is a very long body with 5000 characters of content that goes on and on...'

**Trigger:**

GET /api/search?query=very

**Expected:**

Returns note with truncated/snippet body (e.g., first 200 chars or context around match), not full body

**Concern:**

The endpoint might return the full 5000-char body for every result, which blows up the response size when there are 100 matching notes. Or it might return full body (ticket spec says 'snippet').

**Property:**

For all search results, response body size is O(limit * snippet_size), not O(limit * full_body_size).
