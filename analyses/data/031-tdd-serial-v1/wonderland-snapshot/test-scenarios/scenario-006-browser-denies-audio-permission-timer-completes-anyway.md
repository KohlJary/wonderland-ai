## Scenario 006: Browser denies audio permission; timer completes anyway

**Severity:** degradation

**Setup:**

Marcus's browser has no audio permission granted for this app. Timer countdown displays correctly.

**Trigger:**

Timer reaches completion; code attempts to play audio alert.

**Expected:**

Audio alert fails gracefully (no crash). Visual alert still plays. Console may log a permission warning. Session is marked complete regardless.

**Concern:**

Code throws an exception when playing audio. UI hangs or shows an error. Visual alert doesn't fire because code failed before reaching it.

**Property:**

audio_alert(volume) is idempotent and does not throw on permission denial. Completion always fires visual alert regardless of audio success.
