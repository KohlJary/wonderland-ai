# Contract Note 005-A: Weekly Session Count vs. Daily Consecutive-Day Streak

**State:** proposed
**Seam:** Feature-005 Core Calculation Logic
**Blocker:** Yes — M5 frontend/backend split depends on this choice

---

## The Ambiguity

Story-005 (Kenji) uses language: "how many focus sessions I've completed **this week**" → suggests weekly aggregation.

Contract-note-005 says: "Streak counts **consecutive days**" → suggests daily streak.

These are fundamentally different calculations, UX, and motivation signals.

---

## Option A: Weekly Session Count (Recommended)

**What it is:**
- Sum all completed focus sessions in the current ISO week (Mon-Sun)
- Reset every Monday 00:00
- Display: "4 sessions completed this week"
- No tracking of consecutive days; only total for the week

**Frontend impact (Tweedledee):**
- Query: GET /api/weekly_count (or filter within past 7 days)
- Calculation: sum completed_type='timeout' sessions in current ISO week
- UI state: {loading, empty "0 sessions this week", "N sessions this week"}
- Client state: none (recompute on-demand)
- API contract: `GET /api/weekly_count -> {count: int, week_start_date: string, week_end_date: string}`

**Backend impact (Tweedledum):**
- Event log query: filter sessions by current ISO week (or past 7 days), sum count
- No new calculation logic (just aggregation)
- Timezone handling: week boundary must use user's local time (relevant for Seam-B)

**Matches story intent?** ✓ Yes. Kenji explicitly asks for "this week" count.

**Matches Kenji's persona?** ✓ Yes. He's easily distracted; a weekly mirror (not a daily streak requirement) fits better than a feature that resets if he skips one day.

**Tier alignment?** ✓ Yes. Fast-follow; minimal backend logic.

---

## Option B: Daily Consecutive-Day Streak

**What it is:**
- Count consecutive days (backward from today) on which ≥1 completed session exists
- Reset to 0 the moment any day passes with 0 sessions
- Display: "5-day streak" or "1-day streak"
- Tracks consecutive commitment

**Frontend impact (Tweedledee):**
- Query: GET /api/streak (or full event history)
- Calculation: iterate from today backward, count consecutive days with ≥1 session, stop at first day with 0
- UI state: {loading, empty, "at-risk" (today has 0 so far), "N-day streak"}
- Client state: cache last_completion_date locally (to show status on-app-open without query)
- API contract: `GET /api/streak -> {streak_days: int, last_completion_date: string}`

**Backend impact (Tweedledum):**
- Event log query: return all sessions (or past 30 days), with dates
- Calculation logic: backend could compute streak (simpler for frontend) or frontend computes from raw events (simpler for backend)
- Timezone handling: day boundary must use user's local time (relevant for Seam-B)

**Matches story intent?** ✗ Not directly. Story says "this week" not "consecutive days".

**Matches Kenji's persona?** ✗ Maybe not. He's easily distracted; daily-streak pressure might demotivate rather than motivate.

**Tier alignment?** ~ Unclear. Fast-follow tier, but more UX complexity (showing "at risk" state, handling resets).

---

## Option C: Both (Weekly Count + Daily Streak)

**What it is:**
- Display both metrics: "4 sessions this week" + "3-day streak"
- Reset times differ: weekly resets Monday; daily resets whenever a day is skipped
- Show user both total progress and current momentum

**Frontend impact (Tweedledee):**
- Queries: GET /api/weekly_count + GET /api/streak
- Calculations: both aggregations in parallel
- UI state: combines both sets {loading, empty, "N sessions", "M-day streak"}
- Client state: cache both (last_completion_date for streak, week_session_count for weekly)

**Backend impact (Tweedledum):**
- Event log query: return full event history (or at least past 30 days)
- Calculation logic: both streak and weekly aggregation endpoints
- Complexity: doubles the Seam-B timezone handling (must get it right for both)

**Matches story intent?** ~ Partially. Weekly is core; daily streak is bonus.

**Matches Kenji's persona?** ~ Maybe. Total + momentum could be motivating without pressure.

**Tier alignment?** ✗ No. Fast-follow tier scopes narrowly; Option C is more feature-complete.

---

## Tweedledee's Recommendation

**Go with Option A (Weekly Session Count).**

**Rationale:**
1. Matches story-005 language exactly ("this week")
2. Matches story-005 confusion-flag intent: "no judgment if count is low — it's a mirror, not a report card". Weekly count is a mirror; daily streak is a report card.
3. Simplest backend: just event log aggregation, no streak calculation logic
4. Simplest frontend: query once, display number, no cached state
5. Still achieves Kenji's motivation goal (visible progress) without the pressure

---

## Open Questions for Tweedledum

1. **If Option A:** Can backend provide `GET /api/weekly_count` returning `{count: int, current_week: {start_date, end_date}}`?
2. **If Option B:** Who computes streak — backend or frontend? (Backend is simpler contract; frontend is more offline-capable.)
3. **For all options:** How does Seam-B (timezone) affect the week/day boundary calculation? (See contract-note-005-b.)

---

## Acceptance Condition

Mark this `agreed` when:
- Backend confirms which option is implementable / preferred
- Timezone handling (Seam-B) is separately agreed
- API contract for the chosen option is locked

Until then: all Feature-005 frontend tests skip with explicit reference to this note.
