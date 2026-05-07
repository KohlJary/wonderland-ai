## Scenario 003: Rate limit is per-client, identified by X-Forwarded-For or remote address fallback

**Severity:** breakage

**Setup:**

Two clients, C1 (X-Forwarded-For: 192.168.1.100) and C2 (X-Forwarded-For: 192.168.1.101), both start at same time. Quota is 10 req/min.

**Trigger:**

C1 makes 10 requests. C2 makes 11 requests.

**Expected:**

All 10 from C1 return 200. First 10 from C2 return 200. 11th from C2 returns 429. C1's 11th request still returns 200.

**Concern:**

Silent wrongness: if rate limiting is global, both clients' 11th requests return 429 even though C1 is under quota. Users get false rate-limit errors. If backend ignores X-Forwarded-For and only uses remote address, load-balanced deployments see all clients as same source, making rate-limit useless.

**Property:**

For all clients C1, C2 (C1 ≠ C2), if request_count(C1) < quota and request_count(C2) >= quota, next request from C1 returns 200 and next request from C2 returns 429.

**Implies:**
- Implies contract-002: client ID derivation must be specified and tested explicitly.
