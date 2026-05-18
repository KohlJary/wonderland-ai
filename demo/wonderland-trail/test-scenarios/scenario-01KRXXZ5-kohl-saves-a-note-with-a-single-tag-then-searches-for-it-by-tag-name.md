## Scenario 172: Kohl saves a note with a single tag, then searches for it by tag name

**GUID:** 01KRXXZ5QRD8WJ7NFN2AZWEHWY
**Severity:** silent-wrongness

**Setup:**

Kohl has created and saved a note titled 'Rust Concurrency Notes' with body 'Chapter 3: Arc and Mutex' and a single tag 'rust'. The note is persisted with id=1, and the tag 'rust' exists with id=42.

**Trigger:**

Kohl submits a search query with tags=['rust'] (filtering by tag only, no text query).

**Expected:**

Search results display exactly one note: 'Rust Concurrency Notes' with the 'rust' tag visible in the result chip. The result shows id=1, title, body_preview (first 150 chars of body), created_at, and tags array with {id: 42, name: 'rust'}.

**Concern:**

If the tag association did not persist correctly, the note would appear without its tag, or the search filter would not match the note at all. Kohl would see either an empty result or a note missing its label—both are silent failures (no error message, just wrong data).

**Property:**

Tag association across save and search is consistent

**Implies:**
- tag-association-persists-across-requests
- search-tag-filtering-respects-association-table
- response-includes-tag-ids-and-names
