## Contract Note 005: Duration Validation: Client-Reported vs. Backend-Computed

**State:** deferred
**Contract Version:** (unlocked)

**Current Shape:**

SessionCreate and BreakCreate accept duration_seconds as client input; backend stores it as-is without validating it matches (end_time - start_time). Current request shape: {start_time, end_time, duration_seconds, settings_snapshot}.

**Proposed Change:**

Two options: (1) Backend-computed duration: remove duration_seconds from request, compute it server-side as (end_time - start_time).total_seconds(). Request becomes {start_time, end_time, settings_snapshot}. (2) Client-reported with validation: keep current shape, add Pydantic validator enforcing duration_seconds == (end_time - start_time).total_seconds() (±5 second tolerance for clock skew).

**Source:** Test concern flagged in test_feature_001: 'Without duration validation, malicious client could corrupt history.' Current contract allows POST /api/sessions with start=09:00, end=09:25, duration_seconds=9999 (25 min span claimed as 9999 sec) to be accepted and recorded.

**Frontend Impact (Tweedledee):**

Option 1 (backend-computed): Frontend measures elapsed time (end - start) but doesn't send duration_seconds; backend infers it. I would not need to include duration_seconds in my POST request payload. I would still receive duration_seconds in the response (computed server-side), so history queries remain unchanged. Cleaner contract, one less field to manage. Option 2 (client-reported with validation): I measure elapsed time, include it in POST payload; backend rejects if it doesn't match (end - start). Slightly more work on frontend (one extra field), but preserves current API shape if other systems depend on it.

**Backend Impact (Tweedledum):**

Tweedledum to fill in.

**Resolution:**

deferred. CN-004's decision (backend-computed duration) supersedes this exploratory note. The two-option layout was useful for thinking; the concrete choice is now locked via CN-004.
