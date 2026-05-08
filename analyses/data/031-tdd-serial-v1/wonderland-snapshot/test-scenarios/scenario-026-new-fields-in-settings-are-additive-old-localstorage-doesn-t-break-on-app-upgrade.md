## Scenario 026: New fields in settings are additive; old localStorage doesn't break on app upgrade

**Severity:** degradation

**Setup:**

User has been using the app at version 1.0, with settings stored in localStorage: {focus_duration_ms: 1380000, break_duration_ms: 420000}. App is upgraded to version 1.1, which adds a new field: notifications_enabled (boolean, default true).

**Trigger:**

User opens the app at version 1.1. App reads settings from localStorage.

**Expected:**

The app merges old settings with new defaults: {focus_duration_ms: 1380000, break_duration_ms: 420000, notifications_enabled: true} (default). The app does not crash or lose the old settings.

**Concern:**

If the app expects all fields to be present and fails if notifications_enabled is missing, old localStorage will cause a crash or silent corruption (e.g., undefined fields break the timer logic). Users who upgrade will have a broken experience.

**Property:**

For all settings upgrades that add new fields with defaults, loading old localStorage does not crash and new fields use defaults.
