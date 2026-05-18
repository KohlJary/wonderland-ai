## Scenario 154: Note with 8+ tags and long names renders all badges without horizontal overflow

**GUID:** 01KRXXXVW570ZA3859XC573SKA
**Severity:** degradation

**Setup:**

Search returns a note titled 'ML Experiment' tagged with ['deep-learning', 'pytorch', 'transformer-models', 'fine-tuning', 'transfer-learning', 'nlp', 'bert', 'evaluation-metrics']. Several tag names are 15+ characters. The note's tag section is rendered by renderNoteResult() in Search.tsx.

**Trigger:**

The note appears in search results on a typical desktop browser window (1200px wide).

**Expected:**

All 8 tag badges are visible and readable. Badges wrap across two or more lines if needed using flexbox wrapping (flex-wrap: wrap). No badge text is truncated without an ellipsis indicator. The total height of the tag section is proportional to content (roughly 60px for 2 rows of wrapped badges), and the note item height stays under 250px.

**Concern:**

If the CSS flex container doesn't wrap (or wraps too aggressively), badges could overflow horizontally, get cut off at the viewport edge, or create a very tall tag section. The code uses flexWrap: 'wrap' and gap: 0.4rem, which should work, but the actual rendering under load (with real long tag names) needs verification. Silent wrongness risk: users see truncated tag names and can't read them.

**Property:**

For all notes N with tag_names.length >= 8 where some names are > 15 characters, the rendered tag section displays all tag names in full (no truncation) and wraps gracefully without overflow.

**Implies:**
- Implies frontend layout verification: test the actual Search.tsx resultTags flex container with a variety of tag name lengths and counts. The browser DevTools should show all badges wrapping cleanly.
