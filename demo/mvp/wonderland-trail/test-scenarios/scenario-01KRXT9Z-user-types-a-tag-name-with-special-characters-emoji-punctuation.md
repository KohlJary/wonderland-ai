## Scenario 031: User types a tag name with special characters (emoji, punctuation)

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF7
**Severity:** curiosity

**Setup:**

TagInput focused.

**Trigger:**

User types 'bug🐛' and presses Enter.

**Expected:**

Tag is added as 'bug🐛' (emoji preserved). Chip displays correctly. No rendering errors.

**Concern:**

Component might strip or escape special characters, or fail to render emoji. Unlikely to break in modern React/Unicode, but worth checking.

**Property:**

For all Unicode strings S (including emoji), the component must accept S as a tag name and render it correctly in the chip.
