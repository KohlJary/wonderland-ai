## Scenario: Daily review endpoint receives invalid or malformed date parameter

**Severity:** backend-crash

**Setup:**

User attempts to view daily review for a specific date. Due to a client bug, a user manually editing the URL, or an automated test suite, the date parameter is malformed or invalid (not a valid ISO8601 date).

**Trigger:**

Frontend sends one of:
```
GET /api/daily-review?date=not-a-date
GET /api/daily-review?date=2024-13-01       (invalid month)
GET /api/daily-review?date=2024-02-30       (nonexistent day)
GET /api/daily-review?date=2024-02-31       (Feb has no 31st)
```

Backend receives the malformed date string.

**Expected:**

Backend returns 400 Bad Request with a clear error message, not a 500 Internal Server Error. Valid dates (including leap days like 2024-02-29) return 200 OK.

**Concern:**

If the backend crashes (500) on invalid date input, the daily-review feature becomes unreliable — users cannot view their daily stats. If the backend silently accepts invalid dates or returns wrong data, users will see stale or incorrect aggregates without realizing the date parameter was invalid.

Leap-year boundary dates (Feb 29 in leap years) are a particular edge case: Feb 29 is valid in leap years (2024, 2020, etc.) but invalid in non-leap years (2023). The backend must correctly validate this.

**Property:**

For all valid ISO8601 dates D:
- GET /api/daily-review?date=D returns status 200 OK

For all invalid date strings X (malformed, impossible dates, etc.):
- GET /api/daily-review?date=X returns status 400 Bad Request

For all leap-year dates:
- GET /api/daily-review?date=2024-02-29 returns 200 OK (2024 is a leap year)
- GET /api/daily-review?date=2023-02-29 returns 400 Bad Request (2023 is not a leap year)

**Implies:**

- Implies input validation: the endpoint must parse the date parameter and validate it against the ISO8601 format and calendar rules
- Implies error handling: the endpoint must catch parsing errors and return 400, not crash with 500
- Implies date arithmetic: the backend must correctly identify leap years when validating Feb 29
- Implies testing: test suite must exercise invalid dates, boundary dates (leap days, month boundaries), and past/future dates

**Test Coverage:**

`tests/test_daily_review_fragility.py::TestDateParameterValidation::test_invalid_date_format_returns_400`

`tests/test_daily_review_fragility.py::TestDateParameterValidation::test_malformed_date_like_2024_13_01_returns_400`

`tests/test_daily_review_fragility.py::TestDateParameterValidation::test_nonexistent_date_like_2024_02_30_returns_400`

`tests/test_daily_review_fragility.py::TestDateParameterValidation::test_valid_leap_day_returns_200`

`tests/test_daily_review_fragility.py::TestDateParameterValidation::test_valid_past_date_returns_200`

`tests/test_daily_review_fragility.py::TestDateParameterValidation::test_valid_future_date_returns_200`

`tests/test_daily_review_fragility.py::TestDateParameterValidation::test_missing_date_parameter_returns_400_or_uses_default`
