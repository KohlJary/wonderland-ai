## Scenario 022: Theme can be set to 'light' or 'dark'; invalid values are rejected or normalized

**Severity:** degradation

**Setup:**

User is on Settings screen. theme field is set to 'light'.

**Trigger:**

User tries to set theme to 'light', 'dark', 'auto', 'cosmic', or null. Each attempt is saved.

**Expected:**

Values 'light' and 'dark' are accepted and persisted. Values like 'auto', 'cosmic', null, or missing are either rejected with an error, or normalized to a sensible default (e.g., 'light').

**Concern:**

If arbitrary string values are allowed, the app might try to apply a theme called 'cosmic' that doesn't exist, resulting in a broken UI. Or null/undefined could cause the app to render no theme at all, leaving the user with unstyled content.

**Property:**

For all values assigned to theme, the persisted value is in set {'light', 'dark'}.
