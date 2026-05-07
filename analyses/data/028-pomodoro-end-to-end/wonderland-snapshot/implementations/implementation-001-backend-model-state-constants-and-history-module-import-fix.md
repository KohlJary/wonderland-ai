## Implementation 001: Backend model state constants and history module import fix

**Side:** backend
**Ticket:** m5-implementation
**Contract:** session_lifecycle_timer_state v1, break_lifecycle_state_transitions v1 (state enums: active/completed for sessions, active/skipped/completed for breaks)
**Ready for review:** yes

**Approach:**

Added SessionState and BreakState enums to models.py inheriting from str, so they work with string literal comparisons used throughout the API. Updated history.py to import these constants and use them in session state filtering. All API routers can now load without ImportError.

**Files:**
- src/backend/models.py: added SessionState and BreakState string enums, added backward-compatible class attributes for string literal access
- src/backend/api/history.py: fixed imports to reference SessionState and BreakState, corrected filter queries to use enum constants

**Open Questions for Pair:**
- Are there other API modules that should use these state constants instead of string literals for safety?
