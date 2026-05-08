## Scenario 021: Audio volume is clamped to 0-100 range

**Severity:** degradation

**Setup:**

User is on Settings screen. audio_volume field exists with current value 50.

**Trigger:**

User (or a malformed request, or a script injection) tries to set audio_volume to 150 or -50.

**Expected:**

The app rejects the out-of-range value. Either the UI prevents entry (HTML5 input type=range with min/max), or the app validates on save and shows an error, or silently clamps to the nearest valid value (0 or 100). The setting is not saved with the invalid value.

**Concern:**

If validation is missing, a volume of 150 might cause the audio system to behave unexpectedly (overflow, clipping, or crash). A negative volume is nonsensical. Without validation, localStorage could end up with invalid values that persist across sessions.

**Property:**

For all values V assigned to audio_volume, the persisted value P is in range [0, 100].
