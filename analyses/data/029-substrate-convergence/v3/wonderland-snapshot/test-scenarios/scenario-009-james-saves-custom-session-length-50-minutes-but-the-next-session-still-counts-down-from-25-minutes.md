## Scenario 009: James saves custom session length (50 minutes) but the next session still counts down from 25 minutes

**Severity:** breakage

**Setup:**

James opens Settings, changes Session Length from 25 to 50 minutes, clicks Save (and sees confirmation). He closes Settings and navigates back to the timer screen.

**Trigger:**

James clicks 'Start Session' to verify his custom 50-minute session length.

**Expected:**

The timer countdown begins from 50:00, not 25:00. The displayed duration matches James's saved preference.

**Concern:**

The settings persistence has a seam: either the POST /api/settings write fails silently (frontend thinks it saved, backend didn't), or the Session start endpoint reads stale cached settings instead of fetching fresh from the database, or the settings were written to memory but not the persistent store, and the app restart erased them. James sees the defaults reappear, contradicting the save action. This is breakage because the feature simply doesn't work—James can't customize his timer.

**Property:**

For all settings updates U at time T, any session S started at time T' > T uses the settings written by U, not the prior settings.

**Implies:**
- Requires database-level persistence guarantee—Tweedles own this.
- Implies contract question: does the frontend cache settings, and if so, when does it refresh? Clarify the cache invalidation strategy.
