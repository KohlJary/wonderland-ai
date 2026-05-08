## Scenario 011: Break timer display never shows negative remaining seconds

**Severity:** silent-wrongness

**Setup:**

Break timer is running. Client-side elapsed time is calculated as (now - startTime). Session duration is 600 seconds.

**Trigger:**

600 seconds have elapsed since the break started. Client calculates remaining_seconds = (duration - elapsed). Due to clock skew, elapsed might exceed duration by a millisecond.

**Expected:**

GET /sessions/{id} returns remaining_seconds in range [0, 600]. Never negative. Never wrapping to a huge positive number (e.g., 2^31).

**Concern:**

If remaining is calculated as a signed integer and elapsed > duration, remaining goes negative. If it's unsigned, it wraps. Either way, the UI displays wrong information. Keisha sees '-1 seconds' or '4294967295 seconds' and loses trust in the timer. This is a classic off-by-one in the display layer, but it's silently broken — the API returns the wrong value, and the UI trusts it.

**Property:**

For any session S with duration D and elapsed time E, if E >= D, then remaining_seconds = max(0, D - E) (clamp to 0).

**Implies:**
- Backend-side: when calculating remaining_seconds, clamp to [0, duration].
- Frontend-side: when displaying remaining_seconds, also clamp (belt-and-suspenders).
