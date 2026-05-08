## Scenario 023: audio_enabled flag is boolean; non-boolean values are normalized

**Severity:** silent-wrongness

**Setup:**

User on Settings screen. audio_enabled is currently true.

**Trigger:**

Settings are changed (via UI, or localStorage is manually edited) to audio_enabled: 'true' (string), 1 (number), null, or undefined.

**Expected:**

The app interprets these values safely: 'true' (string) -> true, 1 -> true, null/undefined -> false (or default false). The normalized boolean is what gets persisted and used.

**Concern:**

If the code checks `if (settings.audio_enabled)` and audio_enabled is the string 'false', it will be truthy and audio will play even though the user intended to disable it. Silent wrongness — the app appears to work but produces wrong output (audio plays when it shouldn't).

**Property:**

For all values assigned to audio_enabled, the persisted value is a boolean.
