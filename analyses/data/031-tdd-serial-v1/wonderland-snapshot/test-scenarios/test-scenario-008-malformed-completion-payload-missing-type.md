## Scenario: Session completion endpoint receives malformed payload (missing required field)

**Severity:** backend-crash

**Setup:**

User's client has a session pending completion. Due to a bug in the client (or a compromised client), the completion payload is malformed: the required `type` field is missing.

**Trigger:**

Frontend sends:
```json
POST /api/sessions/session-123/complete
{
  "duration_ms": 1500000
}
```

Backend receives this malformed payload.

**Expected:**

Backend returns 400 Bad Request with a clear error message, not a 500 Internal Server Error and not a silent acceptance of the invalid data.

**Concern:**

If the backend crashes (500) on malformed input, the API becomes a DOS vector — any client can crash the backend by sending garbage. If the backend silently accepts the malformed payload, it enters an inconsistent state: the completion is logged but the type is NULL or default, which breaks the daily-review aggregation (can't distinguish focus vs break).

**Property:**

For all malformed completion payloads P (missing required fields):
- POST /api/sessions/{id}/complete with payload P returns status 400, not 500 or 200

**Implies:**

- Implies schema validation: the endpoint must validate the payload against a schema before processing
- Implies error handling: the endpoint must catch schema validation errors and return 400
- Implies robustness: the endpoint must NOT crash (return 500) on invalid input
- Implies testing: test suite must exercise malformed payloads (missing fields, invalid types, negative numbers, etc.)

**Test Coverage:**

`tests/test_daily_review_fragility.py::TestMalformedInputValidation::test_missing_type_field_returns_400`

`tests/test_daily_review_fragility.py::TestMalformedInputValidation::test_invalid_type_value_returns_400`

`tests/test_daily_review_fragility.py::TestMalformedInputValidation::test_missing_duration_ms_for_focus_returns_400`

`tests/test_daily_review_fragility.py::TestMalformedInputValidation::test_negative_duration_ms_returns_400`

`tests/test_daily_review_fragility.py::TestMalformedInputValidation::test_duration_ms_not_integer_returns_400`

`tests/test_daily_review_fragility.py::TestMalformedInputValidation::test_missing_status_for_break_returns_400`

`tests/test_daily_review_fragility.py::TestMalformedInputValidation::test_invalid_break_status_returns_400`
