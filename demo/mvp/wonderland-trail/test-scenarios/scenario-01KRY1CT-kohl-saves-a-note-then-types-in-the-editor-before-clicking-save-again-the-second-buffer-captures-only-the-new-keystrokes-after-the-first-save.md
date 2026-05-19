## Scenario 318: Kohl saves a note, then types in the editor before clicking Save again—the second buffer captures only the new keystrokes after the first save

**GUID:** 01KRY1CT0KYYZH13BXHBA5K1JK
**Severity:** silent-wrongness

**Setup:**

Kohl saves a note (title: 'Experiment A', body: 'Initial findings'). localStorage is cleared. The editor remains open.

**Trigger:**

Kohl types additional text into the body: ' - More data collected'. She does not click Save again; instead, she closes the tab.

**Expected:**

After the 300ms debounce, localStorage['noteBuffer'] contains {title: 'Experiment A', body: 'Initial findings - More data collected', revisionId: 1} (revisionId from the last saved state). On reload, the editor shows the combined text and Kohl can review it before re-saving.

**Concern:**

If the keystroke handler does not accumulate changes on top of the saved state (e.g., if it clears the entire buffer instead of updating), Kohl will lose the additional text ' - More data collected' on reload. She would see only 'Initial findings', which contradicts her expectation that the buffer captures ongoing edits.

**Property:**

Keystroke buffer accumulates changes after a save; the second buffer session includes both saved content and new keystrokes.
