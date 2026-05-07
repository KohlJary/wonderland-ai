## Contract Note 004: Sessions and Breaks: Backend-Computed Duration

**State:** agreed
**Contract Version:** v2-session-request (start_time: ISO8601, end_time: ISO8601, settings_snapshot: {session_duration_sec: int, break_duration_sec: int}) → response (id, start_time, end_time, duration_seconds: backend-computed, settings_snapshot, created_at); analogous for /api/breaks

**Current Shape:**

(missing)

**Proposed Change:**

(missing)

**Source:** Test concern in test_feature_001: 'Without duration validation, malicious client could corrupt history.' Current design trusts client measurement; agreed change makes backend the source of truth for elapsed time.

**Frontend Impact (Tweedledee):**

Frontend no longer sends duration_seconds in the request. Calculate elapsed time on your side for UX display, but don't send it to the backend—the server will compute and return it in the response. This simplifies the contract and eliminates clock-skew validation complexity.

**Backend Impact (Tweedledum):**

POST /api/sessions and POST /api/breaks no longer accept duration_seconds as input. Backend computes it from timestamps and stores the computed value. Removes the validation risk entirely (no mismatches possible) and simplifies the request contract. Implementation shipped in src/backend/api/sessions.py and src/backend/api/breaks.py with backend-computed duration logic at lines 82-83 (sessions) and 89-90 (breaks).

Also fixed: Type annotations in SessionCreate and BreakCreate now correctly declare start_time and end_time as datetime (post-validator types) instead of str, resolving the type-contract mismatch the Caterpillar flagged. The pre=True validator converts incoming ISO 8601 strings to datetime objects; annotations now reflect the post-conversion types.

**Resolution:** Agreed. Backend implementation complete. Contract version incremented to v2. Ready for frontend pair-off.

**Resolution:**

agreed. Backend computes duration_seconds from (end_time - start_time).total_seconds(). Frontend removes duration_seconds from request payloads; response still includes it (computed server-side). Closes the history-corruption risk the test flagged and simplifies the request contract.
