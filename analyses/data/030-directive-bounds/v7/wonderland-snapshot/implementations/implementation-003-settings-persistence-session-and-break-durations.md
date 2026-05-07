## Implementation 003: Settings persistence (session and break durations)

**Side:** backend
**Ticket:** 
**Contract:** settings-persistence-shape v1 (agreed M3)
**Ready for review:** no

**Approach:**

UserSettings model with session_duration_minutes, break_duration_minutes, timezone. POST /settings to create/update; GET /settings to retrieve. Validates durations are in range [5, 90] minutes. New sessions created after settings change inherit the new durations.

**Files:**
- src/backend/models.py: UserSettings model
- src/backend/api/settings.py: POST /settings, GET /settings endpoints with validation

**Open Questions for Pair:**
- Frontend caching: does frontend cache settings locally and refresh on app startup, or fetch every session creation?
- Settings change mid-session: should in-progress session durations update, or only affect next session? (Test scenarios suggest 'only next session' — confirming.)

**Known Limitations:**
- No optimistic locking on settings updates (concurrent PATCH could lose a field); acceptable for MVP
- Validation is range-only (no business-rule validation like 'break duration < session duration'); open question for frontend
