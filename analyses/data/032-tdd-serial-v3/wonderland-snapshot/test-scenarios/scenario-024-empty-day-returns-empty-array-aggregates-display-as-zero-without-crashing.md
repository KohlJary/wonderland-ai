## Scenario 024: Empty day returns empty array; aggregates display as zero without crashing

**Severity:** degradation

**Setup:**

Dmitri opened the app on a day he did not use it (e.g., 2024-01-10). He has no sessions for that date.

**Trigger:**

Frontend queries GET /sessions?date=2024-01-10. Backend finds no matching records.

**Expected:**

Backend returns { sessions: [], totals: { focusCount: 0, focusMinutes: 0, breakCount: 0, breakMinutes: 0 } } (or equivalent). Frontend displays 'No sessions recorded' or shows zeros without crashing. No division-by-zero errors.

**Concern:**

Backend might return a 500 error when no sessions exist (null-pointer dereference). Frontend might attempt to access the first element of an empty array, crashing. Totals might be undefined, displaying 'undefined minutes' or NaN.

**Property:**

For any date D with no completed sessions, GET /sessions?date=D returns status=200 with empty sessions array and all aggregate counts = 0.
