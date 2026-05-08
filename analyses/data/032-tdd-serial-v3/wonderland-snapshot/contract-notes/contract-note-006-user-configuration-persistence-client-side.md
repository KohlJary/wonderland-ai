## Contract Note 006: User configuration persistence (client-side)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

None — v1 negotiation

**Proposed Change:**

Frontend uses localStorage: focus_duration_seconds (default 1500, range 60–7200), break_duration_seconds (default 300, range 60–1800), sound_enabled (default true). No backend API for settings v1. Settings are device-specific; applied to next session on change.

**Source:** Feature 002 (configurable durations). Features 001, 003 inherit configured values.

**Frontend Impact (Tweedledee):**

I render settings UI (duration spinners, sound toggle). I read localStorage on app start, write on user save. I emit internal settings_changed so timer component applies new defaults to next session.

**Backend Impact (Tweedledum):**

No backend impact v1. Settings are client-local (localStorage). Backend does not store, serve, or sync settings. If Settings API is added in v2, it would be GET /settings and PUT /settings. For now: zero backend involvement. I confirm frontend owns persistence entirely.
