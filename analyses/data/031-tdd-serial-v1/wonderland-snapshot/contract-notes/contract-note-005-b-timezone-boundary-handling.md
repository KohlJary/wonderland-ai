# Contract Note 005-B: Timezone Boundary Handling for Session Aggregation

**State:** proposed
**Seam:** Feature-005 Midnight Boundary Calculation
**Blocker:** Yes — affects Feature-003 (event log) + Feature-005 (streak/count) + Feature-004 (settings)
**Severity:** HIGH — wrong choice causes silent data corruption

---

## The Problem

Contract-note-005 says "midnight boundary is critical" but names three unresolved approaches:
- (1) Backend converts to user local timezone before storing
- (2) Backend stores UTC, frontend converts
- (3) API returns pre-aggregated data (backend owns conversion)

**Example — why this matters:**
- User Kenji is in Pacific Time (UTC-8)
- Kenji completes a session at **23:59 PT on Jan 1**
- In UTC, this is **06:59 UTC on Jan 2** (next morning)
- If backend uses UTC-only date math: session is logged as "Jan 2" → Kenji's weekly count/streak is wrong (counted toward wrong day)
- User doesn't notice immediately; streak/count silently breaks on every late-evening session for all PT/MT/CT users

---

## Option A: Backend Converts to User Local Timezone Before Storing (Recommended)

**How it works:**
1. Feature-004 (Persistent Settings) stores user's timezone (e.g., "America/Los_Angeles")
2. When a session completes, backend reads user's timezone from Feature-004
3. Backend converts completed_at UTC timestamp to user's local timezone
4. Backend stores event with local-timezone-aware timestamp (ISO8601-with-offset, or explicit timezone field)
5. Frontend reads completed_at as already-in-user's-local-perspective; no conversion needed

**Schema example:**
```
Event {
  session_id: uuid,
  user_id: uuid,
  completed_at: "2024-01-01T23:59:00-08:00",  // ISO8601 with offset (user's local time)
  completed_type: "timeout" | "skip",
  duration_ms: int
}
```

**Frontend impact (Tweedledee):**
- API contract: `GET /api/events?from_date=2024-01-01&to_date=2024-01-07` returns events with completed_at already in user's local time
- Calculation: extract local date from completed_at, group by date, sum/streak-count as needed
- No timezone conversion logic needed
- Trustworthy: if event says it was completed at 2024-01-01, I can confidently bucket it into Jan 1 (in user's perspective)

**Backend impact (Tweedledum):**
- Must read user's timezone from Feature-004 (adds a dependency, but Feature-004 is already shipping)
- Must apply timezone conversion during event logging (use standard library like pytz or zoneinfo)
- Must store timezone info in event record (or at least ensure the stored timestamp is consistent with user's local boundary)
- Risk: if timezone is wrong in Feature-004, event boundaries are wrong here too (but that's a Feature-004 problem, not this seam's problem)

**Pros:**
- ✓ Source of truth is clear: event log stores truth in user's perspective
- ✓ Frontend is simple (no conversion logic)
- ✓ Tests can verify directly: event.date should match user's local expectation
- ✓ Offline-first compatible: frontend can work with cached events without network

**Cons:**
- ✗ Backend must know about user's timezone (new dependency on Feature-004)
- ✗ If user changes timezone in settings, historical events are already stored in old timezone (may need migration)

---

## Option B: Backend Stores UTC Only, Frontend Converts

**How it works:**
1. Event log stores completed_at in UTC (ISO8601-with-Z, always UTC)
2. Frontend fetches event: `{completed_at: "2024-01-02T06:59:00Z", ...}` (this is UTC)
3. Frontend fetches user's timezone from Feature-004 settings
4. Frontend converts UTC timestamp to user's local time: 06:59 UTC = 23:59 PT (same local date, Jan 1)
5. Frontend buckets event into correct local date

**Schema example:**
```
Event {
  session_id: uuid,
  user_id: uuid,
  completed_at_utc: "2024-01-02T06:59:00Z",  // always UTC
  completed_type: "timeout" | "skip",
  duration_ms: int
}
```

**Frontend impact (Tweedledee):**
- API contract: `GET /api/events` returns completed_at_utc (always UTC) + API may also include user's timezone as a hint
- Calculation: for each event, convert UTC timestamp using user's timezone, then extract local date, then group/sum/streak as needed
- New logic: timezone conversion (using Intl API or date library like date-fns/dayjs)
- Requires user timezone: must fetch Feature-004 settings before processing events
- Offline complexity: if offline, can't fetch fresh settings; must use cached timezone (risk if user changed timezone)

**Backend impact (Tweedledum):**
- Simpler: just store everything in UTC, no timezone awareness needed
- Event log stores single canonical time (UTC); no migration risk
- Backend doesn't depend on Feature-004

**Pros:**
- ✓ Backend is simpler (everything in UTC, standard approach)
- ✓ No dependency on Feature-004 in backend
- ✓ Single source of truth (UTC is canonical, always consistent)

**Cons:**
- ✗ Frontend must convert (adds logic, adds potential for bugs)
- ✗ Frontend must fetch user's timezone separately (additional roundtrip, offline risk)
- ✗ More places for date-boundary bugs (conversion + grouping + aggregation)
- ✗ Tests are harder to write (must mock timezone conversion)

---

## Option C: Backend Provides Date-Grouped API

**How it works:**
1. Backend provides specialized endpoint: `GET /api/events/grouped-by-date?from_date=2024-01-01&to_date=2024-01-07`
2. Backend does all timezone conversion internally
3. Backend returns events already grouped by user's local date: `{dates: [{date: "2024-01-01", events: [...]}, ...]}`
4. Frontend iterates dates and sums/counts as needed

**Schema example:**
```
GET /api/events/grouped-by-date -> {
  dates: [
    {
      date: "2024-01-01",  // user's local date
      events: [
        {session_id, completed_type, duration_ms},
        ...
      ]
    },
    ...
  ]
}
```

**Frontend impact (Tweedledee):**
- API contract: `GET /api/events/grouped-by-date?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD` returns pre-grouped events
- Calculation: iterate dates, count/streak sessions per date
- Simplest frontend: no timezone logic, no date conversion, just aggregation
- Offline: if events are cached as returned, timezone conversion is already done

**Backend impact (Tweedledum):**
- More complex: backend owns the date grouping logic
- Backend must read user's timezone (Feature-004 dependency, like Option A)
- Backend must convert and group during query (not during storage like Option A)
- Benefit: no schema change needed; just a smarter query endpoint

**Pros:**
- ✓ Frontend is simplest (just iterate and sum/count)
- ✓ Timezone conversion happens once, at query time (not every render)
- ✓ Easier to test: mock the API response, verify frontend aggregation

**Cons:**
- ✗ Backend is more complex (new endpoint, grouping logic)
- ✗ Less flexible: API is opinionated about grouping (can't do custom date ranges easily)
- ✗ More chattier: frontend has to know about the date range upfront

---

## Comparison Table

| Criterion | Option A (Backend Converts at Store) | Option B (Frontend Converts) | Option C (Backend Groups API) |
|---|---|---|---|
| **Timezone aware storage** | ✓ (stored in user's local time) | ✓ (stored in UTC) | ✓ (stored in UTC, grouped on-query) |
| **Frontend complexity** | Low (read & trust) | Medium (convert, group) | Low (iterate & sum) |
| **Backend complexity** | Medium (convert at write, depend on Feature-004) | Low (UTC only) | Medium (convert at query, depend on Feature-004) |
| **Risk of silent data corruption** | Low (converted at source) | Medium (conversion logic in frontend) | Low (converted at query) |
| **Migration risk** | High (if timezone changes, historical events are wrong) | Low (UTC is immutable, only conversion logic changes) | Low (UTC is immutable, query logic changes) |
| **Offline capability** | ✓ Good (events already correct) | ~ Medium (needs cached timezone) | ~ Medium (needs pre-fetched grouped data) |
| **Testing complexity** | Low (direct date assertions) | Medium (mock timezone conversion) | Low (mock API response) |

---

## Tweedledee's Recommendation

**Go with Option A (Backend Converts at Store).**

**Rationale:**
1. Source of truth for session boundaries should live where sessions are stored (backend event log)
2. Frontend should be able to trust the timestamps it receives; no additional conversion logic
3. Test surface is cleaner: test the conversion once in backend tests, then frontend tests are straightforward
4. Risk of silent corruption is lowest (timezone conversion happens once, at the most authoritative point)
5. Matches the principle "events are immutable once logged" — log them correctly the first time

---

## What I Need from Backend

If Option A (recommended):
- Event log stores `completed_at` with timezone offset (ISO8601-with-offset) or separate timezone field
- Backend reads user timezone from Feature-004 Persistent Settings
- Backend converts session completion timestamp to user's local timezone before storing
- API contract: `GET /api/events?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD` returns events with completed_at in user's local perspective

If Option B:
- Event log stores `completed_at_utc` (always UTC, ISO8601-with-Z)
- API contract: `GET /api/events` returns completed_at_utc + user's timezone (or I fetch timezone separately from Feature-004)
- Clear API docs on what "completed_at" means in every response

If Option C:
- New API endpoint: `GET /api/events/grouped-by-date?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`
- Returns events pre-grouped by user's local date
- Backend owns all timezone conversion logic

---

## Open Questions for Tweedledum

1. **Feature-004 integration:** Does Persistent Settings already provide a "get user's timezone" API? Or do I need to call a separate endpoint during Feature-005 frontend work?
2. **Event log timestamp:** Does Feature-003 already store completed_at with timezone info? Or is it just a timestamp?
3. **Performance:** If I choose Option A, does backend need to store timezone in every event row (schema change) or just read it once per user per session?
4. **Backward compatibility:** If users already have events logged without timezone info, how should migration work?

---

## Acceptance Condition

Mark this `agreed` when:
- Backend confirms which option is implementable / preferred
- Feature-003 event log contract is clarified on how completed_at is stored
- Feature-004 settings API is confirmed to provide timezone endpoint
- Clear API contract is locked for the chosen option

Until then: all Feature-005 tests that touch timezone (test_streak_fragility.py::TestMidnightBoundary) skip with explicit reference to this note.

---

## Severity Note

This is marked HIGH because:
1. Data corruption risk: wrong timezone handling silently breaks streak/count for non-UTC users
2. Hidden from user: PT/MT/CT users won't notice immediately (will think the app is buggy)
3. Not easy to test locally: requires running tests in non-UTC timezone
4. Not easy to fix after shipping: historical events are already stored with wrong date boundary

**The tests must pass this seam before M5 ships.**
