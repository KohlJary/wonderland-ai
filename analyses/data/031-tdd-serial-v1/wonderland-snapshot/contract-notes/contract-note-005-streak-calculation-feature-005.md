## Contract Note 005: Streak Calculation (Feature 005)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none

**Proposed Change:**

Streak counts consecutive days on which at least one focus session was completed. Count resets if a day passes with zero completed focus sessions. Weekly view shows session count for the current week (ISO week, rolling). Streak resets if user uninstalls/reinstalls (all data is local; no cross-device persistence). Calculation happens at midnight boundary (same boundary as daily review).

**Source:** story-005 (Kenji wants to see weekly session count as motivation; unclear if monthly too — scoping to weekly only for v1)

**Frontend Impact (Tweedledee):**

UI displays current streak and current week's session count. UI recomputes streak daily (at midnight, or on first session after midnight). UI must handle the case where user opens app after midnight but hasn't completed a session yet (streak shows as 'active but at risk if no session today'). No persistence required beyond local storage.

**Backend Impact (Tweedledum):**

Streak is computed from the event log: 'consecutive days with at least one completed focus session.' Computing this requires backend to know the full event log (or at least, all events for the past N days). Backend provides a query: 'give me all session events for the past 30 days' (or similar window). Frontend computes streak locally. Midnight boundary is critical: events must be tagged with completed_at timestamp in user's local time (or we sync on user's timezone, or we use UTC and frontend converts). Weekly view also requires the full event log. Open question: should backend compute streak for us (simpler contract, backend is source of truth), or should frontend compute from raw events (more frontend logic, backend is simpler)? First option is cleaner; second gives us offline-first capability. Leaning toward first (backend computes, frontend displays), but flagging for your input.
