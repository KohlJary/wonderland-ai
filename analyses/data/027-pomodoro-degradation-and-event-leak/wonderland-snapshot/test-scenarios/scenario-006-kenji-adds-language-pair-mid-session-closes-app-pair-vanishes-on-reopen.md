## Scenario: Kenji adds a language pair mid-session, then closes the app—the new pair vanishes on reopen

**Severity:** silent-wrongness

**Setup:**

Kenji is in an active session with Japanese→English. He adds Chinese→English support (this updates his settings). He does NOT explicitly save or commit the settings change; the settings are in the app's volatile state. He closes the app. He reopens the app hours later and the session is restored.

**Trigger:**

Kenji adds a language pair, then closes the app without an explicit 'save settings' action.

**Expected:**

The new language pair persists. When the session is restored on reopen, Chinese→English is available in the active language list, exactly as Kenji left it. No re-login, no re-configuration.

**Concern:**

The contract specifies that the session record includes `startTime`, `targetDuration`, `completionStatus`, etc., but does not explicitly specify that settings (language pairs) are *part* of the session persistence surface. If the backend assumes 'settings are user-global' rather than 'settings as part of this session's state envelope,' then mid-session changes might not be tied to the session record itself. When the session is restored (by session ID), the settings might load from 'current user settings' rather than 'settings as they were at session creation.' Result: Kenji's new pair is lost.

**Property:**

For all settings changes made during an active session, those settings must be recoverable by restoring the session, even if the settings were not explicitly committed to a separate 'settings' entity. Settings are part of the session's state envelope.

**Implies:**

- Implies architectural decision: are settings (language pairs, duration defaults, etc.) part of the session record, or are they global user state? The contract notes mention 'settings changes mid-session' but don't clarify ownership or persistence boundary. Flag for Cheshire Cat.
- Implies Kenji/Tweedledum backend responsibility: if settings are not in the session record, they need to be captured at session creation time or persisted as a session attribute so reopen can restore them.
- Implies Alice: the stories all assume settings changes persist as part of the session, but the contract doesn't name where or how. Clarify: are settings part of the session or separate?

