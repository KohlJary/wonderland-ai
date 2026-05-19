## Scenario 065: Kohl types for 30 seconds without hitting Save, then accidentally closes the tab and reopens it; her draft is restored from localStorage

**GUID:** 01KRXTE35W88GEZR30A8W5VQ4D
**Severity:** degradation

**Setup:**

Kohl has an open editor with an empty note (not yet saved). localStorage is enabled

**Trigger:**

Kohl types title 'Experiment results' and body 'We found that...' (about 150 chars of typing). She does NOT click Save. She closes the tab or navigates away. She reopens the app within the same browser session

**Expected:**

The editor restores the title and body from localStorage. There is a clear visual indication (e.g., 'Unsaved draft' banner) that this is a draft, not a persisted note. Kohl can click Save to persist, or Clear to discard and start fresh

**Concern:**

If the draft is not restored, Kohl loses 30 seconds of work to accidental tab closure. This is a known expectation from the keystroke-buffer requirement. If the draft is restored but Kohl doesn't see it is a draft (no visual cue), she might think it's persisted when it is not, leading to later confusion

**Property:**

localStorage survives page reload; unsaved state is visually distinguished from persisted state

**Implies:**
- Editor component saves title and body to localStorage on every keystroke (debounced ~500ms)
- On mount, editor checks localStorage and restores if present
- Visual indicator shows whether the note is saved (id exists) or unsaved (no id, in localStorage only)
