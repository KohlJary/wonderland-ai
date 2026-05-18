## Scenario 290: User loses power or browser crashes during a typing burst—latest keystroke is not necessarily persisted

**GUID:** 01KRY1AH3KPSQ1N168XD0XCQTS
**Severity:** curiosity

**Setup:**

Editor with 500 char body buffered in state but not yet flushed to localStorage (still within debounce window).

**Trigger:**

Device loses power or browser tab is forcibly closed.

**Expected:**

On restart, localStorage still contains the previous state (before the typing burst), because the debounce window never closed. The user sees their work from before the burst, not the burst itself. This is an acceptable tradeoff for the ticket design (keystroke-level durability is not promised, only debounced state durability).

**Concern:**

Ticket accepts this: 'keystroke buffer' means 'buffered state', not 'every single keystroke persisted'. User understands page reload may lose a few seconds of work if the browser crashes mid-burst. The 300ms debounce is the boundary of durability the system promises.
