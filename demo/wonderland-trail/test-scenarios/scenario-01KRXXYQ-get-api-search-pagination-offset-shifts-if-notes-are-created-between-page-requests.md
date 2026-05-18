## Scenario 171: GET /api/search pagination offset shifts if notes are created between page requests

**GUID:** 01KRXXYQD08R1GFPSWEN113274
**Severity:** curiosity

**Setup:**

50 notes exist. User requests page 1 (page_size=20). While reading, 10 new notes are added. User requests page 2.

**Trigger:**

GET /api/search?page=1&page_size=20, then 10 notes created, then GET /api/search?page=2&page_size=20.

**Expected:**

Page 2 returns notes based on current order. Some notes from page 1 might reappear on page 2 if new notes are more recent. Acceptable for eventually-consistent pagination.

**Concern:**

Offset-based pagination is vulnerable to dataset mutations between requests. If the dataset grows, offset shifts. Known limitation of offset-based pagination, not a bug.

**Property:**

Offset-based pagination is eventually consistent; users may see duplicate rows or miss rows if the dataset changes during pagination.
