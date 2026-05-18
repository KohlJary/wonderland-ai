## Scenario 271: If-Match header is missing from a PUT request, the endpoint returns 400 Bad Request (client error) rather than silently ignoring the header and saving anyway

**GUID:** 01KRY19VMP015JW631HNJ74GC5
**Severity:** breakage

**Setup:**

Client sends PUT /notes/1 with a valid new state but omits the If-Match header entirely.

**Trigger:**

PUT /notes/1 with body {title: 'new', body: 'content'} and no If-Match header.

**Expected:**

Backend returns 400 Bad Request with detail 'Missing required If-Match header for collision detection'. The note is not modified.

**Concern:**

If the backend accepts a save without If-Match, it's allowing blind writes without collision detection, which defeats the entire purpose of the contract. The frontend might forget to send the header (bug in frontend), and the backend should catch this and reject it, not silently proceed.

**Property:**

For all PUT /notes/{id} requests, the If-Match header is required. If missing, the request is rejected with 400 Bad Request. This is a strict requirement from the contract.

**Implies:**
- Requires If-Match header validation in the PUT endpoint — flag for Tweedledum.
- Requires test coverage that verifies PUT without If-Match returns 400.
