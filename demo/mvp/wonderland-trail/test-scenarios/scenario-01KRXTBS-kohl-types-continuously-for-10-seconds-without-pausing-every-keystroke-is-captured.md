## Scenario 053: Kohl types continuously for 10 seconds without pausing; every keystroke is captured

**GUID:** 01KRXTBSX1SQXPMXS4J54GRZBQ
**Severity:** silent-wrongness

**Setup:**

Kohl opens the editor with blank fields. She has a block of 500 words about rust memory safety ready to paste or type rapidly.

**Trigger:**

Kohl types or pastes the 500 words continuously, keystroke after keystroke, for 10 seconds without pausing. The editor is keeping up with the keystroke stream.

**Expected:**

All 500 words appear in the body field. The text is not truncated, jumbled, or missing words. localStorage buffer (after the debounce window closes) contains the complete 500-word text. If Kohl reloads immediately after finishing, all 500 words are restored.

**Concern:**

If the keystroke debounce is too short, or if the component re-renders without preserving state, rapid typing could lose characters. Or if localStorage writes are asynchronous and not awaited, a reload immediately after rapid typing could lose the tail of the text. Kohl would notice she's missing words and lose trust in the feature.

**Property:**

keystroke buffer handles rapid input without dropping characters

**Implies:**
- user-types-rapidly-20-keystrokes-per-second-no-keystrokes-are-dropped-and-all-content-is-saved
