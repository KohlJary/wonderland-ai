## Scenario 247: GET /notes returns empty array when no notes exist

**GUID:** 01KRY190Z3094B2DF4C3RP2H59
**Severity:** curiosity

**Setup:**

Fresh app state. Database is empty. localStorage is also empty.

**Trigger:**

Frontend calls GET /notes on boot.

**Expected:**

GET /notes returns 200 with empty array [].

**Concern:**

The contract says GET /notes returns empty array if no notes, but the code doesn't check for this explicitly — it just returns all results, which could be []. This is correct, but I want to verify the response shape is truly [] and not null.

**Property:**

For all states of the database, GET /notes returns an array (possibly empty), never null or undefined.
