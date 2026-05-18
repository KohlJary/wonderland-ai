## Scenario 018: Preview updates in real-time as user types a markdown heading

**GUID:** 01KRXT9P2QWG3M7HXFBYEWFK7C
**Severity:** breakage

**Setup:**

A markdown editor with a preview pane to its right. The editor's body field contains '# Hello'. The Preview component receives body as a prop.

**Trigger:**

The user types an additional '#', changing the body to '## Hello'.

**Expected:**

The preview pane immediately re-renders, showing the content as an H2 instead of an H1. No lag between keystroke and preview update.

**Concern:**

React might batch updates but preview delay would be perceived as broken. I'm concerned that if the preview re-renders too slowly, Kohl will think the component is sluggish even if it's technically correct.

**Property:**

For all markdown input M, if body prop changes to M', preview renders M' before the next React frame (within ~16ms for 60fps). Real-time means no perceivable lag.
