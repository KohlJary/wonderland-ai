## Scenario 316: Kohl types in the title field and expects localStorage to include the title change alongside body content

**GUID:** 01KRY1CT0KYYZH13BXHBA5K1JH
**Severity:** silent-wrongness

**Setup:**

Kohl opens the editor. localStorage has a prior entry: {title: 'Experiment A', body: 'Previous notes', revisionId: null}. The editor restores this state.

**Trigger:**

Kohl modifies the title to 'Experiment A - Refined Results' (25 characters added), then stops typing.

**Expected:**

After the 300ms debounce window closes, localStorage['noteBuffer'] is updated with {title: 'Experiment A - Refined Results', body: 'Previous notes', revisionId: null}. Both fields are persisted correctly.

**Concern:**

If the keystroke handler only buffers body changes and ignores title changes, Kohl's title edit is lost on reload. She will see her old title 'Experiment A' reappear, losing her refinement.

**Property:**

Keystroke buffer captures changes to both title and body fields.
