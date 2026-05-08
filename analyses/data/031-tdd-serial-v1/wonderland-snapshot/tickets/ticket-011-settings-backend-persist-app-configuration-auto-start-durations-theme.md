## Ticket 011: Settings backend: persist app configuration (auto-start, durations, theme)

**Sources:** persistent-settings
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: settings-ui-frontend
- Blocked by: session-persistence-backend
- Soft: —

**Description:**

Backend API and storage for app-wide settings. Simple key-value store (or settings table). Expose GET/PUT endpoints for the frontend. Scope: auto-start break (boolean), default break duration (minutes), theme (string). Defaults provided if settings are uninitialized.

**Acceptance:**
- GET /settings returns current app settings with sensible defaults
- PUT /settings with a settings object persists and returns the updated settings
- Settings survive an app restart

**Risk:**

Low. This is a trivial store.
