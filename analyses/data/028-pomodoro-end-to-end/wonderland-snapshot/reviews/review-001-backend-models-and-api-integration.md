## Review 001: Backend models and API integration

**Files reviewed:** src/backend/models.py, src/backend/api/history.py, src/backend/api/statistics.py, src/backend/api/__init__.py
**Verdict:** block

### Findings

#### block: Unresolved imports: SessionState and BreakState enums
**Location:** src/backend/api/history.py:10
**Quote:**

```
from src.backend.models import Session, SessionState, Break, BreakState, User
```

**Read:** The history.py module attempts to import SessionState and BreakState as enums from models.py, then uses them on lines 52, 69, 108, 132 (e.g., Session.state == SessionState.completed). These enums do not exist in models.py — the Session and Break models use string literals ('active', 'completed', 'skipped') for state, not enum values.
**Concern:** This import error will cause the module to fail at import time. The entire history.py file, including the /sessions/history endpoint that correctly tracks break duration and skip status, will be unreachable. Tests will fail with ImportError.
**Request:** Either: (a) Define SessionState and BreakState enums in models.py and update Session and Break model state columns to use them, OR (b) Replace SessionState and BreakState references in history.py with string literals ('completed', 'skipped'). Given that statistics.py uses string literals and works, option (b) is the minimal fix. Change lines 52, 69, 108, 132 from SessionState.completed / BreakState.skipped to 'completed' / 'skipped'.

#### block: Duplicate route registrations for /stats/week and /stats/all-time
**Location:** src/backend/api/__init__.py:8-18
**Quote:**

```
api_router.include_router(history_router)
api_router.include_router(statistics_router)
```

**Read:** Both history.py (lines 103-125, 133-157) and statistics.py (lines 51-75, 78-102) define handlers for GET /stats/week and GET /stats/all-time. When both routers are registered without prefixes, the second registration (statistics_router) overwrites the first (history_router). The statistics.py version will be the active handler.
**Concern:** The history.py endpoint for /stats/week correctly queries sessions and calculates total_duration_seconds as sum of elapsed time (s.completed_at - s.start_time), matching Feature 004 requirements. The statistics.py version computes total_duration_seconds as sum(s.duration_minutes * 60), which is the configured duration, not actual elapsed. History.py's version is correct. Silently using the wrong version causes incorrect statistics to be served.
**Request:** Remove statistics.py entirely, or remove the duplicate endpoint handlers from statistics.py and keep only the user endpoint (/user, lines 154-165). The history.py module already defines all necessary stats endpoints. If statistics.py is retained for some future purpose, prefix its router registration differently (e.g., include_router(statistics_router, prefix='/stats-alt')) to avoid collision.

#### change-required: history.py /user endpoint duplicates user.py /user endpoint
**Location:** src/backend/api/history.py:154-165
**Quote:**

```
@router.get("/user", response_model=UserResponse)
def get_user(db: DBSession = Depends(get_db)) -> UserResponse:
    """Get user profile information."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return UserResponse(**user.to_dict())
```

**Read:** The history.py module defines a GET /user endpoint at the end. User.py (lines 35-50) also defines GET /user with nearly identical logic, computing days_tracked server-side in the same way.
**Concern:** Two handlers registered for the same route will collide. One will be overridden. The user.py version is cleaner (separate file, focused purpose); history.py's version should be removed to avoid ambiguity.
**Request:** Delete the /user endpoint definition from history.py (lines 154-165). The user.py router will provide it.

### Approvals

- Session lifecycle code (sessions.py) is well-structured: idempotency on start/stop is correct, launch_date set only on first session, break auto-created with user's configured duration.
- Break state machine (breaks.py) properly handles idempotency on skip: checks state before transition, returns early if already skipped/completed.
- Settings API (settings.py) uses validation (ge=1, le=180) and partial updates correctly; settings always exist due to _get_or_create_settings pattern.
- History endpoint in history.py (when imports are fixed) correctly associates breaks with sessions and computes actual elapsed duration from timestamps, not configured duration.
- Frontend App.tsx demonstrates good separation of concerns: navigation bar controls view state, polling logic for session/break status is clean, settings/history/stats views are conditional renders with proper loading states.
- Frontend api.ts correctly mirrors backend routes and types; error handling includes status code checks; endpoints use proper HTTP methods (POST for actions, GET for reads, PATCH for partial updates).

### Cross-domain references

- The SessionState/BreakState import error is a code correctness issue; no architectural question for the Cat.
- The duplicate route registration is also code correctness, not architectural.
- All defined endpoints match the contracted features; no scope concerns for Alice or the Rabbit.
