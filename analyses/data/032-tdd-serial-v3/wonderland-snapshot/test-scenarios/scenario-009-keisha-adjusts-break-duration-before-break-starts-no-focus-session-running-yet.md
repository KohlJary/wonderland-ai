## Scenario 009: Keisha adjusts break duration before break starts (no focus session running yet)

**Severity:** breakage

**Setup:**

Focus session is running. Break timer has not yet started (focus is still active, ~2 minutes remaining).

**Trigger:**

Keisha opens settings and changes break duration from 300 to 900 seconds. Focus session then ends.

**Expected:**

When focus completes, the break timer starts with 900 seconds (the new setting), not 300. No race between setting-update and auto-start.

**Concern:**

If the break timer is queued or pre-calculated during focus, a late setting change might not propagate. If settings are read only once at app startup, changes mid-session won't be visible until next app launch. Keisha's story says 'adjust without losing my default', implying changes take effect next session. But does 'next session' mean 'immediately after current session ends' or 'next app launch'? Assuming immediate.

**Property:**

Let D1 = break duration at app start, D2 = break duration after user updates settings mid-focus-session. When the focus session ends, the break timer's configured duration should be D2, not D1.

**Implies:**
- Depends on how frontend caches vs. reads settings. If settings are a singleton loaded once, mid-session updates won't apply. If settings are read fresh on each session end, they will.
- No backend implication (settings are client-local per Contract-002).
