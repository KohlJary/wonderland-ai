## Contract Note 007: User settings persistence and CRUD

**State:** agreed
**Contract Version:** v1 (settings-persistence-crud)

**Current Shape:**

Settings schema: session_length_sec (default 1500), break_length_sec (default 300), notification_enabled (bool, default true), sound_enabled (bool, default true). Frontend can GET/POST/PATCH settings; changes take effect on next session (in-flight session ignores changes). Settings are user-scoped (implicit in auth context).

**Agreed Changes:**

Settings persistence and CRUD as proposed, with additional validation constraints (see contract-004 for validation policy).

**Frontend Impact (Tweedledee):**

I'll fetch settings on app startup via GET /settings and cache in memory + localStorage. Settings UI is a settings page with: session duration slider (5–60 min, validated on client), break duration slider (1–30 min, validated on client), toggle switches for notifications and sound. When user adjusts a slider or toggle: (1) immediately update local state and UI, (2) kick off async PATCH /settings with the new values, (3) if PATCH succeeds, confirm success silently, (4) if PATCH fails (400/422 for validation, 5XX for server error), show error banner with retry option and revert the UI. If GET /settings fails on app startup, I'll use hardcoded defaults and show a 'settings unavailable' indicator until sync succeeds.

**Backend Impact (Tweedledum):**

Backend provides GET /settings and PATCH /settings endpoints. GET /settings returns current user's settings (or defaults if not yet set): { session_length_sec, break_length_sec, notification_enabled, sound_enabled }. PATCH /settings accepts a partial update (one or more fields) and returns the updated settings object. Validation: enforce bounds on session_length_sec (300–3600) and break_length_sec (60–1800); see contract-004 for detailed validation requirements. Settings are user-scoped (user_id implicit from auth context). Settings are mutable (unlike sessions, which are immutable facts).

**Agreed By:** Tweedledee and Tweedledum (resolved in test-scenarios thread)
**Date:** M4, test-scenarios

**Notes:**

Partial updates: PATCH supports updating a subset of fields. If a field is omitted, it retains its previous value.

Notification and sound flags are frontend UI toggles; backend stores them but does not enforce policy (frontend is responsible for actually sending notifications or playing sounds). Backend simply persists the user's preference.

Changed fields apply to the next session only. In-progress sessions continue with the settings they were initialized with, even if settings are changed via PATCH during the session.
