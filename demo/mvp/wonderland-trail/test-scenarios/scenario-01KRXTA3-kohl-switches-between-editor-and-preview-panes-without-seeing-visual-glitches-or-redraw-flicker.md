## Scenario 038: Kohl switches between editor and preview panes without seeing visual glitches or redraw flicker

**GUID:** 01KRXTA3XPB15WS3APKGDFPEWA
**Severity:** degradation

**Setup:**

Kohl has a long markdown note (500+ chars) open in the editor. The preview pane is visible on the right. She's actively typing and watching the preview.

**Trigger:**

Kohl types continuously for 10 seconds, then pauses and scrolls in the preview pane to read earlier content, then resumes typing.

**Expected:**

The preview pane updates smoothly as she types. When she scrolls in the preview, the scroll position is preserved when she types again. No flicker, no jumping layout, no 'jank' (frame drops or stuttering). The split-pane layout stays stable and responsive.

**Concern:**

If the preview thrashes (redraws on every keystroke with visible flicker), Kohl's eyes are constantly caught by motion and she can't focus on writing. If scrolling causes layout shifts or the pane jumps back to the top, the UX is frustrating.

**Property:**

Smooth, flicker-free split-pane rendering with scroll stability

**Implies:**
- preview-scroll-position-is-preserved-on-continued-editing
- no-layout-shift-or-jank-on-preview-update
