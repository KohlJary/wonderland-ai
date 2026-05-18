## Scenario 210: Search query with 10,000 notes in storage, user types single character

**GUID:** 01KRXYEG9WMJ0GPZ2FAHJSYB4T
**Severity:** degradation

**Setup:**

SQLite database contains 10,000 notes with varied titles and bodies. User has typed 'a' in search box.

**Trigger:**

GET /api/notes/search?q=a fires

**Expected:**

Endpoint returns within 500ms with notes matching 'a' in title or body, paginated or streamed to avoid memory spike.

**Concern:**

Naive substring search on 10,000 notes will do 10,000 string scans per character typed. If user types five characters, that's 50,000 scans. Response latency will degrade to seconds, and the frontend may time out or freeze.

**Property:**

For all N notes in storage and query string Q, search latency must remain sub-500ms even when len(N) > 5000 and len(Q) = 1.

**Implies:**
- Implies architectural decision about pagination / streaming — flag for Cat if response strategy is unclear.
- Implies performance testing harness needed — flag for Dormouse for production baseline.
