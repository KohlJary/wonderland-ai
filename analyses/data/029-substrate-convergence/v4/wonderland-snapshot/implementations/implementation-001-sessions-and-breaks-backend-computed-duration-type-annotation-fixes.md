## Implementation 001: Sessions and Breaks: Backend-Computed Duration + Type Annotation Fixes

**Side:** backend
**Ticket:** feature-001, feature-002
**Contract:** v2 (backend-computed-duration): POST /api/sessions and POST /api/breaks accept only start_time (ISO 8601), end_time (ISO 8601), and settings_snapshot. Backend computes and returns duration_seconds.
**Ready for review:** yes

**Approach:**

Removed duration_seconds from SessionCreate and BreakCreate request models. Backend now computes duration_seconds from end_time - start_time at POST time and stores it. Fixed type annotations on start_time and end_time to declare datetime (post-validator type) instead of str. Both POST endpoints and response models updated.

**Invariants Enforced:**
- Duration is always non-negative: computed from end_time - start_time, and Pydantic validator ensures end_time >= start_time
- Duration matches elapsed time by construction: backend computes it, not trusted from client
- Settings snapshot is immutable: captured at creation, stored as JSON, never updated

**Schema Changes:**

No new migrations required. Sessions and Breaks tables already have duration_seconds column. No schema changes to the DB itself. Request/response contract changes only.

**Failure Modes Handled:**
- end_time < start_time: Rejected by Pydantic validator, returns 400
- Missing or malformed timestamps: Pydantic parse_datetime validator handles ISO 8601 parsing and Z suffix, returns 422 on parse failure
- IntegrityError from DB constraint: Caught and wrapped in 400 Bad Request

**Files:**
- src/backend/api/sessions.py: Updated SessionCreate to remove duration_seconds field, fixed type annotations, added server-side duration computation at line 82-83. Updated docstring to explain v2 contract.
- src/backend/api/breaks.py: Updated BreakCreate to remove duration_seconds field, fixed type annotations, added server-side duration computation at line 89-90. Updated docstring to explain v2 contract.
- src/backend/api/__init__.py: Registered sessions_router and breaks_router (existing change; included for completeness).

**Known Limitations:**
- No time-zone handling beyond UTC assumption; both frontend and backend assume all times are UTC.
- Duration is computed via int() cast, truncating fractional seconds; acceptable for this feature.
