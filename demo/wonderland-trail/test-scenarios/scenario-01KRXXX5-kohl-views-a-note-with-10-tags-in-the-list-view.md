## Scenario 146: Kohl views a note with 10+ tags in the list view

**GUID:** 01KRXXX5EYSQXB8M7T8022QXTM
**Severity:** degradation

**Setup:**

Kohl has created a note and (during research) added 15 tags to it: 'rust', 'performance', 'async', 'concurrency', 'memory', 'benchmarking', 'optimization', 'systems', 'lowlevel', 'cpu', 'io', 'threading', 'scheduling', 'latency', 'throughput'. She opens the list view.

**Trigger:**

The list view renders the note with all 15 tags.

**Expected:**

The tags display without wrapping off the screen or overflowing the note card. The list view remains scannable (no horizontal scroll required on typical screen width). If horizontal space is limited, tags degrade gracefully: either wrapping to a second row, truncating with a '+N more' indicator, or appearing on hover.

**Concern:**

If tags overflow or cause the note card to expand excessively, the list view becomes cramped and scanning many notes becomes difficult. Kohl's list becomes hard to use if one tag-heavy note takes up half the screen.

**Property:**

Tag display must be responsive and handle high tag counts without breaking list-view layout.

**Implies:**
- Tag badges must wrap or truncate intelligently when space is constrained.
- List view must remain vertically scannable even when a note has many tags.
- Horizontal overflow must not force scrolling (or if it does, it should be clear and non-intrusive).
