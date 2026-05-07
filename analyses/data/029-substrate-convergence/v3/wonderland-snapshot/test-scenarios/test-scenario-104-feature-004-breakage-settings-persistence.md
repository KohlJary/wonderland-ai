# Test Scenario 104: Feature 004 — Breakage: Settings Persistence

**Feature:** Customize session and break lengths to fit personal rhythm
**Severity:** breakage
**Concern:** The settings persistence has a seam: either the POST /api/settings write fails silently (frontend thinks it saved, backend didn't), or the Session start endpoint reads stale cached settings instead of fetching fresh from the database, or the settings were written to memory but not the persistent store, and the app restart erased them. James sees the defaults reappear, contradicting the save action. This is breakage because the feature simply doesn't work—James can't customize his timer.

## Scenario

James opens Settings, changes Session Length from 25 to 50 minutes, clicks Save (and sees confirmation). He closes Settings and navigates back to the timer screen.

James clicks 'Start Session' to verify his custom 50-minute session length.

## Expected

The timer countdown begins from 50:00, not 25:00. The displayed duration matches James's saved preference.

## Failure Mode

The settings save endpoint returns success but the write doesn't persist to the database. Or: the session start endpoint reads cached settings that haven't been refreshed. Or: the settings are written to memory only, and an app restart erases them. Result: James sees the defaults reappear.

## Property

For all settings updates U at time T, any session S started at time T' > T uses the settings written by U, not the prior settings.

## Test Implementation

See `tests/test_feature_004_settings_persistence.py` for runnable tests.

## Implies

- Requires database-level persistence guarantee—Tweedles own this.
- Implies contract question: does the frontend cache settings, and if so, when does it refresh? Clarify the cache invalidation strategy.
