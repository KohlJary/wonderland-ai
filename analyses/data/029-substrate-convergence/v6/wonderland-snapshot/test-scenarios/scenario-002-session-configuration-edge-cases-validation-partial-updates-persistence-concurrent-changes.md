## Scenario 002: Session configuration edge cases — validation, partial updates, persistence, concurrent changes

**Severity:** breakage

**Setup:**

Sam adjusts lengths repeatedly: valid updates (50 min), invalid (0, negative, out-of-range >120), and partial PATCHes where only one field is provided.

**Trigger:**

PATCH /config with valid and invalid session_length_minutes values. PATCH with only session_length (omitting break_length). Verify GET /config returns current state. Verify next session uses new default.

**Expected:**

Valid updates (1–120 session, 1–60 break) return 200 OK, persist, and apply to next session. Invalid inputs return 400. Partial PATCH preserves omitted fields. GET /config returns all current values.

**Concern:**

Zero or negative duration accepted, breaking timers. Partial PATCH resets omitted fields to default. Type coercion: string '50' accepted, masking API violation. Config cached globally across users. No error message indicating valid range.

**Property:**

PATCH /config with V ∈ [1–120 session, 1–60 break] → 200, persists V. GET /config returns V. Omitted fields retain previous values. For sessions S started after PATCH, S.target_duration = V.session_length * 60.

**Implies:**
- Implies input validation with clear error messages naming valid range
- Implies atomic PATCH (transactional; no partial updates to database)
- Implies per-user config storage (not global shared state)
- Implies immediate effect (no server restart required)
