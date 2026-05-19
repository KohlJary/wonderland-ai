## Scenario 035: Kohl pastes a markdown draft with headers and lists, sees live preview render within 100ms

**GUID:** 01KRXTA3XPB15WS3APKGDFPEW7
**Severity:** silent-wrongness

**Setup:**

Kohl has the editor open with an empty body field. The preview pane is visible on the right side of the split layout.

**Trigger:**

Kohl types a markdown draft: '# My Findings

- First observation
- Second observation

## Details

More text here.'

**Expected:**

As Kohl types each character, the preview pane updates to show the rendered HTML: heading level 1, unordered list with two items, heading level 2, paragraph. The preview visibly updates within 100ms of each keystroke (feels instant to her). No lag or flicker.

**Concern:**

If the preview doesn't update in real-time, Kohl has to constantly switch mental context between 'what I'm typing' and 'what it will look like.' Real-time rendering is the core feature; if it's slow or batched, the flow breaks.

**Property:**

Live markdown rendering with sub-100ms latency on keystroke
