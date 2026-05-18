## Scenario 249: GET /notes scales to 100 notes sub-100ms without N+1 queries

**GUID:** 01KRY190Z3094B2DF4C3RP2H5B
**Severity:** degradation

**Setup:**

Database contains 100 notes, each with 3 tags (300 tag associations total).

**Trigger:**

Frontend calls GET /notes.

**Expected:**

GET /notes returns all 100 notes with all tag information (tag_names and tag_ids) in under 100ms. Query count should be O(1) or at worst O(2) (one for notes, one eager load for tags), not O(N).

**Concern:**

The current code uses SQLAlchemy relationship loading, which could trigger N+1 if tags are not eagerly loaded. When note.tags is accessed in the loop (via to_dict()), SQLAlchemy may issue a query per note if the relationship is not joined or eager-loaded.

**Property:**

For any query result size N, GET /notes must complete in constant time relative to database round trips (i.e., at most 2 round trips regardless of N).

**Implies:**
- Implies potential N+1 query on tags relationship — flag for Tweedledum to optimize with eager loading or joinedload.
