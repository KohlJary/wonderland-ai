## Scenario 033: Uninstall/reinstall same day, sees streak = 0 (expected per local-only contract, bad UX)

**Severity:** degradation

**Setup:**

Derek: 7-day streak. Uninstalls app. No cloud backup (local-only per contract). Reinstalls same day before midnight.

**Trigger:**

Derek opens app after reinstall, navigates to streak.

**Expected:**

Streak = 0. Correct per contract but bad UX (Derek just hit 7 days, lost it). Known limitation for v1 (fast-follow tier).

**Concern:**

UX more than bug. Derek feels betrayed. For v1 acceptable; future versions might add cloud sync. Test should verify streak resets (expected), not preserve it (violates contract).

**Property:**

Streak = function(local_event_log). Event log cleared on uninstall. Therefore streak = 0 after reinstall.

**Implies:**
- Implies design: is local-only acceptable, or should v1 include account/cloud sync?
- Implies test fixture: simulate app uninstall (clear local storage, reinitialize)
