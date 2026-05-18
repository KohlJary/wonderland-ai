## Scenario 027: User removes a chip by clicking the X button

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF3
**Severity:** breakage

**Setup:**

TagInput with three chips: 'rust', 'embedded', 'testing'. Each chip has an X button.

**Trigger:**

User clicks the X button on the 'embedded' chip.

**Expected:**

The 'embedded' chip is removed. The remaining chips are 'rust' and 'testing'. Internal state is tag_names: ['rust', 'testing'].

**Concern:**

Click handler on the X button might not be wired, or might remove the wrong chip (wrong index), or might not update the component state.
