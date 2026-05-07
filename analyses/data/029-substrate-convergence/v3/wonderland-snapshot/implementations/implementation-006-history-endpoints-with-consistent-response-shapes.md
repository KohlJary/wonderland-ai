## Implementation 006: History endpoints with consistent response shapes

**Side:** backend
**Ticket:** 004
**Contract:** contract-note-004 (Feature 002: today count), contract-note-006 (Feature 003: historical aggregation)
**Ready for review:** yes

**Approach:**

/api/session-history/today: individual SessionRecords for today. /api/session-history/weekly: daily aggregates (8 days). /api/session-history/all-time: all individual SessionRecords (newest-first). /api/session-counts/{today,weekly}: count + duration aggregates. All filter focus-only, breaks excluded.

**Invariants Enforced:**
- Focus-only: breaks excluded from counts and aggregates
- Completed-only: in-progress Sessions not included
- Date boundaries: UTC midnight to midnight
- Missing dates: zero-filled (not null)

**Schema Changes:**

None; uses existing SessionRecord table

**Failure Modes Handled:**
- No sessions today: returns count=0 (not 404)
- Empty history: returns empty list with proper structure
- Fractional minutes: rounded down via int()

**Files:**
- src/backend/api/history.py: Fixed /api/session-history/all-time to return individual records (not aggregates)

**Known Limitations:**
- UTC timezone only (no user timezone parameter; v1 limitation)
- No pagination (returns all records; acceptable for v1 single-user)
- No caching (every GET queries DB fresh, per contract)
