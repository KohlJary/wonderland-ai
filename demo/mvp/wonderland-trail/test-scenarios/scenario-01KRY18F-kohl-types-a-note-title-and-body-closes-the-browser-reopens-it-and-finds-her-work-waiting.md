## Scenario 242: Kohl types a note title and body, closes the browser, reopens it, and finds her work waiting

**GUID:** 01KRY18F88GKW92A57SY2C1JVM
**Severity:** breakage

**Setup:**

Kohl has the note editor open with an empty title and body. localStorage is empty.

**Trigger:**

Kohl types 'Experimental fusion approach' in the title field, then switches to the body and types 'Temperature gradient suggests...' as her first draft. She gets interrupted and closes the browser tab entirely.

**Expected:**

When Kohl reopens the app moments later, the title field reads 'Experimental fusion approach' and the body reads 'Temperature gradient suggests...' — exactly what she typed before closing. No API call happens; the data comes from localStorage.

**Concern:**

If the debounce fails or localStorage doesn't actually persist across browser close, Kohl loses work mid-thought. This is the core durability promise of the feature — it has to work reliably or the whole thing fails her trust.

**Property:**

localStorage round-trip survives browser close
