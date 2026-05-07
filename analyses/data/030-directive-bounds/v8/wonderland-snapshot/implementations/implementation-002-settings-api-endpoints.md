## Implementation 002: Settings API endpoints

**Side:** backend
**Ticket:** feature-002
**Contract:** contract-002: /api/settings GET/POST. Request body and response via SettingsRequest/SettingsResponse. X-Session-ID header required. Auto-create defaults on first access. Both fields required on POST.
**Ready for review:** yes

**Approach:**

Settings model persists focus_minutes and break_minutes per session_id in DB. GET /api/settings returns current or creates defaults (25/5). POST /api/settings upserts validated values. Validation: focus_minutes > 0, break_minutes >= 0, both ≤ 999.

**Invariants Enforced:**
- Settings row is unique per session_id (upsert semantics)
- Focus minutes always > 0; break minutes always >= 0
- Both fields required on POST (no partial updates)

**Schema Changes:**

No migrations; using existing Settings model with unique constraint on session_id.

**Failure Modes Handled:**
- Missing X-Session-ID header → 400
- Missing focus_minutes or break_minutes on POST → 422
- Invalid duration values → 400
- First access to non-existent settings → auto-create with defaults (25/5)

**Files:**
- src/backend/api/settings.py: Complete settings management endpoints
- src/backend/api/__init__.py: Included settings_router in api_router

**Known Limitations:**
- Settings are global per session_id, not per-device or per-user-account (anonymous session design)
- No settings versioning; overwrites are destructive
