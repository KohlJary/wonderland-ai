## Scenario 301: User deletes entire localStorage while editor is open and typing; next keystroke saves stale data

**GUID:** 01KRY1ARRE8QYC9GT63D0YD5H0
**Severity:** silent-wrongness

**Setup:**

Editor is open with title='Ideas' and body='First para about async'. localStorage contains {title: 'Ideas', body: 'First para about async', tags: []}. Another tab or external process clears localStorage entirely (e.g., user runs `localStorage.clear()` in console, or a service worker clears cache).

**Trigger:**

User types 'Second para' into the body field. The keystroke handler reads the current state from React (which is unaffected by the localStorage.clear) and tries to write it back: localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({...})).

**Expected:**

The keystroke writes {title: 'Ideas', body: 'First para about async Second para', tags: []} to localStorage. The editor continues to work. When Kohl closes and reopens, the editor restores the state including the new keystroke.

**Concern:**

This scenario may actually work as intended — React state is the source of truth, localStorage is the shadow. However, if another tab expects to read from localStorage and finds nothing (because it was cleared), that tab will load a blank editor. This is a footgun for multi-tab scenarios. Not a breakage of the single keystroke, but a consistency hazard.

**Property:**

The keystroke buffer must handle external clears of localStorage without crashing or losing React state.

**Implies:**
- Implies: the editor's React state is the real source of truth; localStorage is a secondary backup. This is good design, but worth documenting.
- Implies: multi-tab scenarios are fragile if one tab clears localStorage while others are reading.
