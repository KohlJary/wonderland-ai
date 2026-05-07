## Scenario 007: Concurrent publishes to same slug: authorization and write are atomic

**Severity:** breakage

**Setup:**

User A (unauthorized to write /~bob) and User B (authorized) both issue POST /homepage/bob simultaneously.

**Trigger:**

Two concurrent POST requests to the same slug, one from authorized user, one from unauthorized.

**Expected:**

Authorized write succeeds, unauthorized write fails (403). No authorization-check-then-act race window.

**Concern:**

Authorization check at T0 might pass, but by T10 (when write executes) user might be unauthorized. Check-then-act race leads to privilege escalation.

**Property:**

For all homepages H and users U: POST /homepage/:slug is atomic. Authorization check and write cannot be separated in time.
