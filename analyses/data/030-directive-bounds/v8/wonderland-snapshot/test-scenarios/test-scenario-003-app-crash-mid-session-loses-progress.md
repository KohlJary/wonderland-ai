## Test Scenario: App crash mid-session with no state persistence means timer progress is lost

**Severity:** degradation

**Feature:** Feature 001: Run a focus session with breaks

**Setup:**

User has started a focus session 12 minutes ago (elapsed_time=720). current_session lives only in backend memory (no DB write yet). App crashes or browser tab refreshes.

**Trigger:**

Frontend reconnects and makes GET /sessions/current request.

**Expected:**

Backend has no record of the session (lost state). Frontend receives 404 or empty response. User must restart the session. The 12 minutes of work are not credited.

**Concern:**

This is a tradeoff from the contract: transient state in-memory means crash = full loss. Contract accepted this (on restart, no resume). But the severity classification matters: is this 'degradation' (user has to start over, but no data corruption) or 'breakage' (app appears broken)? Classifying as degradation: expected behavior per contract, just not pleasant.

**Property:**

For all current_session states, if backend process exits, session state is not recoverable from disk (by contract design).

**Implications:**

None noted.
