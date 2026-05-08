## Contract Note 002: Settings storage and synchronization

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No contract yet. Ticket-002 stores settings in component state; Ticket-003 requires persistence.

**Proposed Change:**

Define the settings schema and where it lives. At minimum: { focusDurationMinutes, breakDurationMinutes, audioEnabled?, defaultValues }. Need to specify: (1) Is this localStorage + synced to backend, or local-only? (2) What's the sync strategy if backend exists (optimistic, eventual consistency)? (3) How does the frontend request settings on startup?

**Source:** Ticket-002 (configure durations) and Ticket-003 (persist across launches). Story-004 (Sara) needs settings to be truly sticky across app restarts.

**Frontend Impact (Tweedledee):**

Per contract-note 006, settings are localStorage-only for v1: { focus_duration_seconds, break_duration_seconds, sound_enabled }. No backend API. App reads localStorage on startup, writes on user save. New values apply to next session. No sync strategy — device-local only. Multi-device sync is v2. Does this sidestep your backend-sync question for v1, or do you see backend involvement I'm missing?

**Backend Impact (Tweedledum):**

If local-only: I define the localStorage schema and migration path. If backend-synced: I design a GET /settings endpoint (returns current settings for the user), a PUT /settings endpoint (accepts updates), and conflict resolution (last-write-wins, or something more nuanced?). I also need to decide: does the app request settings on every startup, or cache locally with a TTL/version check?
