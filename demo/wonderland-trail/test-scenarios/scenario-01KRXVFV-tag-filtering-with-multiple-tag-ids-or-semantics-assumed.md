## Scenario 077: Tag filtering with multiple tag IDs (OR semantics assumed)

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9H
**Severity:** breakage

**Setup:**

Notes: A(work), B(personal), C(work+personal), D(home)

**Trigger:**

GET /api/search?query=&tag_ids=<work-id>,<personal-id> (comma-separated or array format)

**Expected:**

Returns notes A, B, C (all have at least one of the two tags), excludes D

**Concern:**

The API contract doesn't specify multiple tags syntax (comma-separated string, JSON array, repeated param). The code might expect only one tag, or might AND instead of OR, or might fail to parse multiple tags.

**Property:**

For all sets of tag IDs T, search with tag_ids=T returns notes that have at least one tag in T.

**Implies:**
- Implies contract ambiguity — the ticket says 'tag filtering' but doesn't specify multiple-tag semantics. Flag for Cat or Rabbit to clarify the contract.
