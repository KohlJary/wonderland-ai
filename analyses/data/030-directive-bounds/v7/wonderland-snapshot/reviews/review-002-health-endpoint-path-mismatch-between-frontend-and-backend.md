## Review 002: Health endpoint path mismatch between frontend and backend

**Files reviewed:** frontend/src/api.ts, src/backend/api/__init__.py
**Verdict:** request-changes

### Findings

#### block: Frontend calls /api/health but backend health router doesn't use /api prefix
**Location:** frontend/src/api.ts:170-174
**Quote:**

```
export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch('/api/health');
  if (!res.ok) {
    throw new Error(`checkHealth failed: ${res.status}`);
  }
  return res.json();
}
```

**Read:** The checkHealth function calls fetch('/api/health'). In src/backend/api/__init__.py, health_router is mounted with api_router.include_router(health_router) without a prefix argument. The health router defines @router.get('/health'), so the actual path is /health, not /api/health. All other routers (sessions, settings, export) use prefix='/api'.
**Concern:** The fetch request to /api/health will receive a 404 error. Any code calling checkHealth() will fail. The endpoint path inconsistency will break health checks and confuse future maintainers about API organization.
**Request:** Fix src/backend/api/__init__.py: change api_router.include_router(health_router) to api_router.include_router(health_router, prefix='/api'). This aligns all API routes under /api/ and matches the frontend's expectations.

### Approvals

- Backend router structure is consistent across sessions, settings, and export endpoints

### Cross-domain references

- tests/test_health.py may expect /health path; verify after backend fix that tests still pass
