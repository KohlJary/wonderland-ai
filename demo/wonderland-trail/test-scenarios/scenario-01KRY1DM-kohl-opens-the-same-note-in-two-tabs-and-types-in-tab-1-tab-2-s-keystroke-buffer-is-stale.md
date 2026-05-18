## Scenario 342: Kohl opens the same note in two tabs and types in Tab 1; Tab 2's keystroke buffer is stale

**GUID:** 01KRY1DM2GCZ9MKM8TTD72W1P7
**Severity:** silent-wrongness

**Setup:**

Kohl has saved a note (id=5, title='Experiment Log', body='Day 1 results'). She opens Tab 1 (editor for note 5) and Tab 2 (same note 5). Both tabs load the note and populate their keystroke buffers with the same initial state. Tab 1's localStorage key is 'editor_draft_5'; Tab 2's localStorage key is also 'editor_draft_5' (they share the same key because they're editing the same note).

**Trigger:**

In Tab 1, Kohl types 'Day 2 results' and the keystroke buffer writes 'Day 1 results...Day 2 results' to localStorage. In Tab 2 (which has not been focused), Kohl types 'Addendum' and the keystroke buffer writes 'Day 1 results...Addendum' to localStorage, silently overwriting Tab 1's buffer.

**Expected:**

On reload, localStorage contains only Tab 2's buffer. Tab 1's 'Day 2 results' keystroke are lost. Kohl had two versions in progress and only one survives — the last-tab-to-write wins, silently discarding the other.

**Concern:**

Multi-tab collision is not detected by the keystroke buffer. If Kohl is switching between two tabs and typing in both, the last-write-wins behavior silently overwrites her draft. This is a silent-wrongness: no error or warning; the user's work just vanishes.

**Property:**

keystroke-buffer-is-not-tab-aware

**Implies:**
- concurrent-keystroke-buffers-in-two-tabs-collide
- no-warning-when-keystroke-buffer-is-overwritten-by-another-tab
