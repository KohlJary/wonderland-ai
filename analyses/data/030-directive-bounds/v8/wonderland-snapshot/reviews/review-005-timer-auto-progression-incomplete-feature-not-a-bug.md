## Review 005: Timer auto-progression: incomplete feature, not a bug

**Files reviewed:** src/backend/api/sessions.py
**Verdict:** request-changes

### Findings

#### suggestion: elapsed_time never increments; phases don't auto-transition—document design limitation
**Location:** src/backend/api/sessions.py:115-128
**Quote:**

```
_current_sessions[session_id] = {
    "elapsed_time": 0,
    ...
}
```

**Read:** Session state is in-memory only. When started, elapsed_time is 0. No mechanism increments it or transitions phases. GET /api/sessions/current returns the same elapsed_time forever. The tests skip the timer cases with 'requires background timer mechanism...'
**Concern:** Feature 001 claims 'automatically break when the timer ends,' which requires server-side time tracking. Current implementation supports manual pause/resume/complete but not automatic progression. This is a known design gap (tests skip it), but it's not documented in code or contracts. Future developers will be confused about why the feature is incomplete.
**Request:** Add a contract note or ticket documenting that auto-timer and phase transition are deferred work. This ensures the team knows the limitation is intentional, not a bug.

### Cross-domain references

- Architectural decision required: transient in-memory state vs. persistent state with background workers. Requires a design ticket for timer service / background scheduler.
