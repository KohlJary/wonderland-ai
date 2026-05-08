## Contract Note 004: Settings Store (Feature 004)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none

**Proposed Change:**

Settings store holds user preferences: focus_duration_ms (default 25*60*1000), break_duration_ms (default 5*60*1000), audio_enabled (boolean), audio_volume (0-100), theme (light/dark). Settings persist across app close/reopen. Settings are readable and writable by frontend. Settings have sensible defaults; on first run, defaults are applied.

**Source:** story-004 (Yuki's custom timings 23/7 must persist across sessions; defaults on new device are reasonable but not pinned)

**Frontend Impact (Tweedledee):**

UI has a settings screen with editable fields for durations, audio, theme. UI can read current settings and apply them to new sessions. Changing settings takes effect immediately (next session uses new durations). No sync across devices required for v1 (per ADR local-first decision).

**Backend Impact (Tweedledum):**

Settings are client-side local storage only in v1. Backend has zero responsibility here. No persistence, no sync, no server-side validation. (If future versions add cross-device sync, this changes; note it as tech debt / v2 consideration.) For now: empty backend.
