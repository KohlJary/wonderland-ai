## Scenario 156: Tag name with emoji renders without mojibake or replacement characters

**GUID:** 01KRXXXVW570ZA3859XC573SKC
**Severity:** curiosity

**Setup:**

A note is tagged with ['🔬research', '🔗link', '📝draft']. The note appears in search results.

**Trigger:**

renderNoteResult() renders the tags as badge elements with the emoji-containing tag names.

**Expected:**

Each emoji renders correctly adjacent to the text. No replacement characters (U+FFFD), no mojibake, no double-width corruption. All three badges render clearly and readably.

**Concern:**

Emoji handling in small UI elements (badge pills) can have quirks in some browsers, especially with variable-width emoji or zero-width joiners. While React/JavaScript typically handles unicode well, edge cases (surrogate pairs, emoji sequences, RTL marks) can cause silent rendering bugs. This is a curiosity test to verify robustness.

**Property:**

For all tag_names T containing emoji, the rendered resultTag displays T without corruption or mojibake.
