## Scenario 001: Client clock drift >5s triggers resync to server time

**Severity:** silent-wrongness

**Setup:**

Marcus starts 25-min session, client caches {start_time, remaining_seconds}. Client's clock 8 seconds fast relative to server.

**Trigger:**

Client computes elapsed via local clock math. On next poll, server returns authoritative remaining_seconds.

**Expected:**

Client detects |client_remaining - server_remaining| > 5s, resyncs to server value. Display shows server truth.

**Concern:**

If client trusts local clock without syncing, timer drifts from reality. User sees 4:30 remaining (client) but server says 4:22. Silent wrongness: UI appears correct but is untethered from reality.

**Property:**

For all polls of /session/current, if (client_remaining - server_remaining) > 5s, client must resync to server_remaining.
