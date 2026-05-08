## Implementation 001: Persistent Settings v1 — localStorage-backed SettingsManager + SettingsScreen UI

**Side:** frontend
**Ticket:** feature-004
**Contract:** Settings object: {focus_duration_ms: positive int, break_duration_ms: positive int, audio_enabled: boolean, audio_volume: 0-100 int, theme: 'light'|'dark'}. Storage key: 'app_settings'. No backend involvement in v1. Partial updates merge with current state. Validation: on load + before save. Defaults: 25min focus, 5min break, audio on, volume 50, light theme.
**Ready for review:** yes

**Approach:**

SettingsManager is a client-side class that reads/writes Settings to localStorage with validation. Invalid values (negative durations, out-of-range volumes, unknown theme) are normalized or rejected. Unknown fields are ignored (forward compatible). Save is partial-merge, not full-replace. onChange() subscribers are notified after successful save. SettingsScreen is a React component wrapping the manager: form state, error display, change detection, theme application. Settings object never lives out of sync between manager and storage.

**UI States Implemented:**
- loading (on first mount, settings load from storage)
- empty (no settings saved yet, defaults shown)
- editing (form filled with current settings, unsaved changes detected)
- error-recoverable (save failed, error message shown, retry available)
- saving (disabled buttons, visual feedback while save in flight)
- success (save completed, form cleared/locked until next change)

**Client State:**

Form state lives in React component (formState); settings live in SettingsManager singleton; synchronized via onChange listener. On unmount, any unsaved form changes are discarded (user must explicitly Save). No client-side cache of settings except in-memory manager instance.

**Files:**
- frontend/src/settings.ts: SettingsManager class with localStorage integration
- frontend/src/SettingsScreen.tsx: React component for settings UI
- frontend/src/__tests__/settings.test.ts: unit tests (Vitest)
- frontend/src/App.tsx: updated to include SettingsScreen and route between views

**Open Questions for Pair:**
- No backend contract needed for v1 (local storage only). Confirm this is the design intent.

**Known Limitations:**
- No cross-device sync (v1 design: local storage per device, independent)
- No backend persistence (v1 design: client-side only)
- Theme changes require manual save; no auto-save on every field change
