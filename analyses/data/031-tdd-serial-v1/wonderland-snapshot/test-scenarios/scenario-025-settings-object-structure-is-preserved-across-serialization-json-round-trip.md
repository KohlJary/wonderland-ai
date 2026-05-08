## Scenario 025: Settings object structure is preserved across serialization (JSON round-trip)

**Severity:** silent-wrongness

**Setup:**

Settings object is created with keys: focus_duration_ms, break_duration_ms, audio_enabled, audio_volume, theme.

**Trigger:**

Settings are saved to localStorage (JSON stringified) and reloaded (JSON parsed). This happens multiple times across multiple app sessions.

**Expected:**

The loaded settings object has the same keys and types as the original. No keys are dropped, no types are corrupted (e.g., strings don't become numbers or vice versa).

**Concern:**

If the serialization/deserialization is naive (e.g., missing quotes in JSON, or manual string concatenation instead of JSON.stringify), the loaded object could be missing keys, or have the wrong types. For example, a settings load could fail silently, leaving the app with partial or undefined settings, which could cascade to a broken session timer (e.g., calling `session_duration = settings.duration_ms` when duration_ms is undefined).

**Property:**

For all settings objects S serialized to localStorage and deserialized back, the loaded object == S (same keys, same types, same values).

**Implies:**
- Implies JSON serialization (JSON.stringify on save, JSON.parse on load) is used, not manual string concatenation.
