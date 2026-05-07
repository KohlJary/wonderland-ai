## Ticket 005: Implement session and break history list view

**Sources:** review-focus-history
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: persistent-storage
- Soft: custom-duration-settings

**Description:**

Build the history view: list of past sessions and breaks, showing date, start time, duration, and outcome (completed / paused). Reverse chronological order. Fetch from backend storage, format for display. Persona here is someone who wants to *see what they've accomplished* — make the list scannable and satisfying. No editing, no deletion; history is read-only.

**Acceptance:**
- History list displays all past sessions and breaks
- Each entry shows date, time, duration, and state
- List is sortable by date (newest first by default)
- List loads from persistent storage on app open
- Performance is acceptable (< 1 sec) for 100+ session records

**Risk:**

If history grows large (1000+ records), list rendering may slow. Implement pagination or virtual scrolling if needed — defer to post-launch if v1 testing shows no issue.
