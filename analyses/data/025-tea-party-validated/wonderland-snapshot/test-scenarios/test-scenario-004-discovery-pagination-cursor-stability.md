## Scenario: Discovery listing — cursor pagination stability under concurrent updates

**Severity:** silent-wrongness (users see duplicate or missing results when browsing discovery)

**Setup:**

The discovery endpoint returns paginated results of recent homepages:

```
GET /discover?limit=10&cursor=<opaque_cursor>
→ { homepages: [...], next_cursor: "..." }
```

The contract specifies: "Cursor is opaque (backend encodes updated_at + id for stable pagination). Ordered by updated_at DESC."

Alex is browsing discovery. They request the first page (no cursor), which returns 10 results. While Alex is reading those results, Priya publishes a new homepage. Alex clicks "load more" and sends the cursor from the first page.

**Trigger:**

Backend decodes the cursor. It contains a cutoff point (e.g., updated_at of the oldest result from the first page). Backend queries for homepages with updated_at < cutoff, ordered by updated_at DESC, limit 10.

But Priya's new homepage has updated_at > cutoff (it's newer). So it's not included in the second page. It might not appear until Alex reaches the third page, or it might appear in the first page if Alex refreshes—creating the illusion that Alex saw it before.

**Expected:**

1. **Cursor stability** — Once Alex has a cursor, it defines a fixed position in the timeline. Subsequent pages are consistent with that position. If new homepages are published, they are not retroactively inserted into earlier pages (causing Alex to see them out of order). Instead, they appear on refresh of the first page.
2. **No duplicates** — A homepage that appeared on page N should not appear again on page N+1 (unless the sorting key changed).
3. **No silently missing items** — All homepages in the system should eventually be discoverable (though they might appear in different order depending on when browsing started).
4. **Boundary correctness** — If a homepage's updated_at exactly matches the cursor boundary, it appears on one page and only one page. No off-by-one errors.

**Concern:**

Pagination with a sorting key (updated_at) that can change (when users update their homepages) is notoriously tricky. Common failure modes:

1. **Keyset pagination not implemented** — Cursor-based pagination is naive: just an offset (page 2 = skip 10, return 10). When new items arrive, this shifts: the items on page 2 shift down, and items from page 1 might re-appear on page 2.
2. **Inclusive boundary** — Cursor encodes updated_at=timestamp. Query is `updated_at < timestamp`. But if two homepages have updated_at exactly equal to timestamp, one is included and one is excluded unpredictably (depends on secondary sort key like id).
3. **Tie-breaking failure** — When two homepages have the same updated_at, which one comes "first" in the sort order? If that's not defined (e.g., no id-based tie-break), then the sort order is undefined and pagination can skip items.
4. **Cursor tampering** — If cursor is not truly opaque (e.g., it's decoded on the client), users can manipulate it to skip forward/backward in ways the server doesn't expect.

The contract says cursor is "opaque" and encodes "updated_at + id for stable pagination". This is correct. But implementation details matter.

**Property:**

For all users U, homepages H = {H1, H2, ..., Hn} sorted by (updated_at DESC, id ASC):

When U browses discovery with sequential cursor-based pagination starting at position i:

1. Page i contains homepages H[i:i+limit].
2. Page i+1 contains homepages H[i+limit:i+2*limit].
3. No homepage appears in more than one page.
4. The set of all pages (union of results across all cursors) contains exactly H (all homepages, each exactly once).
5. The order is consistent: if Hi appears before Hj on page P, then Hi appears before Hj on all pages where both are visible.
6. Concurrent updates (new homepages, edited homepages) do not cause pages already viewed to change.

**Implies:**

Implies database query design (Tweedledum's domain—keyset pagination vs. offset pagination). Implies contract refinement: is the tie-breaker id-based? Can users edit their homepage and change its updated_at? (If yes, that invalidates previous cursors, which is acceptable but should be documented.) Implies test coverage for pagination under concurrent updates (which is hard to test deterministically).

---

## Notes for Test Implementation

The pytest tests will:

1. Create multiple homepages with different updated_at timestamps.
2. Fetch /discover?limit=3 (page 1).
3. Create a new homepage.
4. Fetch /discover?cursor=<from_page_1>&limit=3 (page 2).
5. Assert no duplicates across pages.
6. Assert the new homepage appears either on page 1 (if refresh) or on a later page, but not in the middle of the sequence.
7. Test tie-breaking: create two homepages with identical updated_at and verify they are ordered consistently by id.

This test will FAIL until pagination is implemented with keyset logic (cursor-based with tie-breaker).
