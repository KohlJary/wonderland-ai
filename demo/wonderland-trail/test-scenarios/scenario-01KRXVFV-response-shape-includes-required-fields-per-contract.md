## Scenario 085: Response shape includes required fields per contract

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9S
**Severity:** breakage

**Setup:**

Any valid search query

**Trigger:**

GET /api/search?query=test

**Expected:**

Response includes id, title, content/body (or snippet), tags, created_at, updated_at for each result. Matches NoteResponse shape (or a variant).

**Concern:**

The response might be missing fields, or might return the full Note object without pagination metadata. Contract ambiguity: does 'paginated results with note metadata' mean an array, or {results: [], page_count: X}?

**Property:**

For all search results, each result object contains {id, title, content_or_snippet, tag_names, tag_ids, created_at, updated_at}.

**Implies:**
- Implies contract ambiguity on response shape — is it an array or an object with metadata? Flag for Cat or Rabbit.
