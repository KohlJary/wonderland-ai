## Scenario 012: Break duration defaults to 5 minutes, configurable per session

**Severity:** degradation

**Setup:**

User is starting a break timer. No duration preference has been set (feature 004 settings not yet available).

**Trigger:**

Focus session completes and break auto-starts without explicit duration parameter.

**Expected:**

Break session receives duration_seconds=300 (5 minutes) by default. If user has customized break duration in settings (feature 004), that value is used instead.

**Concern:**

Contract says 'default 5 minutes, configurable' but doesn't specify where the default lives (backend hardcode vs. frontend default). Feature 004 is separate. On first break before settings, where does the 300 come from?

**Property:**

Every break session has a duration_seconds value. Without explicit configuration, duration_seconds=300.
