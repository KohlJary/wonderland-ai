## Test Scenario 022: Settings validation rejects out-of-range values with clear error messages

**Severity:** breakage

**Feature:** Feature 004: Customize session and break lengths to fit personal rhythm

**Setup:**

James opens the Settings screen. The current values are focus_session_length=25, break_length=5 (defaults). He decides to test the validation by entering some extreme values.

**Trigger:**

James enters the following values and taps Save:
1. focus_session_length = 0 (below minimum of 1)
2. break_length = 121 (above maximum of 60)
3. focus_session_length = -5 (negative)
4. focus_session_length = "abc" (non-numeric)

**Expected:**

For each invalid input, the backend returns a 400 Bad Request with a response shape:
```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": {
    "field_name": "reason"
  }
}
```

Examples:
- focus_session_length: 0 → "must be >= 1"
- break_length: 121 → "must be <= 60"
- focus_session_length: -5 → "must be >= 1"
- focus_session_length: "abc" → "must be an integer"

The Settings in the DB are not modified. The user sees a clear error message on the UI (not a generic "something went wrong").

**Concern:**

If the backend doesn't validate input ranges, a user could set focus_session_length to 0 or 5000 minutes. A 0-minute session would break the timer logic (countdown would be instant). A 5000-minute session might be accepted but not practically usable.

If the error message is vague (e.g., "Invalid input"), the user won't know what went wrong or how to fix it.

If the frontend doesn't enforce validation (relying only on backend validation), and the user is on a slow connection, they might tap Save multiple times, causing race conditions or multiple failed requests.

**Property:**

For all Settings POST requests:
- focus_session_length in [1, 120]
- break_length in [1, 60]
- Both must be integers
- Any out-of-range value returns 400 with detailed error messages
- Settings are never updated if validation fails

**Implies:**

This tests the input validation contract (contract-note-005) for the Settings endpoint. The scenario validates that the backend enforces the constraints and provides clear feedback.

