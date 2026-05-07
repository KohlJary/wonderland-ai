## Test Scenario 006: Payload Size Limit — Content Over 1MB Rejected

**Severity:** degradation

**Setup:**

User has POSTed valid markdown multiple times (all under 1MB). System works smoothly. Now user attempts to upload markdown over 1MB (e.g., a very large blog post with extensive history or quotes).

**Trigger:**

User POSTs {content: 'x' * (1024 * 1024 + 1)} (1MB + 1 byte).

**Expected:**

Backend rejects with 413 Payload Too Large. Response includes {error: 'payload_too_large', message: 'Content must be under 1MB'}. No partial storage, no corruption.

**Concern:**

Without size limits, a malicious user could upload gigabytes of content, exhausting disk space, causing denial-of-service, and potentially crashing the server. Contract-003 specifies: "Content size limit: 1MB max (enforced at request body parsing layer before markdown parsing)."

This is a degradation scenario (not breakage) because the system still functions; the user simply can't upload files over 1MB. But it's a necessary limit to prevent abuse.

**Property:**

All POST /homepage/:slug requests with content > 1MB must be rejected at the HTTP body parsing layer (before markdown parsing begins).

**Implies:**

- Requires HTTP server configuration or middleware to enforce max request body size (FastAPI middleware, nginx config, etc.).
- Requires early rejection (return 413 at HTTP layer, not after markdown parser runs).
- Implies test data: use a string > 1MB to trigger the limit.
