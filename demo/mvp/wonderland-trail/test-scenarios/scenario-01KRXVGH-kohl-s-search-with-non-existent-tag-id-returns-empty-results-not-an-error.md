## Scenario 092: Kohl's search with non-existent tag ID returns empty results, not an error

**GUID:** 01KRXVGHT2Y73C5JV7SEK1JJ7A
**Severity:** degradation

**Setup:**

Kohl accidentally sends tag_id=9999 (which doesn't exist) in her search request. Maybe she bookmarked an old link or a tag was deleted.

**Trigger:**

Kohl's search request includes tag_ids=[9999].

**Expected:**

The endpoint returns {total_results: 0, page: 1, page_size: 20, results: []} without error. The response is 200 OK, not 400 or 404. Kohl sees 'No results' instead of a crash or error message.

**Concern:**

If the endpoint returns 400 'Tag not found', Kohl is confused—why is a filter a client error? If it crashes with 500, the search feature is unreliable. Silent empty results are more graceful and match user expectations for a filter that matches nothing.

**Property:**

Non-existent tag IDs result in empty results, not errors
