## Scenario 314: Kohl types a 50-character note in the body field and expects localStorage to capture the keystroke within 300ms

**GUID:** 01KRY1CT0KYYZH13BXHBA5K1JF
**Severity:** silent-wrongness

**Setup:**

Kohl opens the editor with an empty body field. No localStorage entry exists yet. The component mounts and sets up the debounce handler.

**Trigger:**

Kohl types 'Here are my initial thoughts on the experiment result' (50 characters, typed over ~3 seconds).

**Expected:**

After the last keystroke, the debounce timer runs to 300ms without another keystroke. localStorage['noteBuffer'] is updated once with {title: '', body: 'Here are my initial thoughts on the experiment result', revisionId: null}. The entry persists so a page reload before clicking Save will restore this text.

**Concern:**

If the debounce does not work correctly—either because it fires on every keystroke (thrashing localStorage) or because it never fires (text is lost on reload)—Kohl's recovery guarantee is broken. She expects her typing to survive an accidental page close or browser crash, but if localStorage is not written, the text vanishes.

**Property:**

Keystroke buffer writes to localStorage at most once per 300ms debounce window, not on every keystroke.
