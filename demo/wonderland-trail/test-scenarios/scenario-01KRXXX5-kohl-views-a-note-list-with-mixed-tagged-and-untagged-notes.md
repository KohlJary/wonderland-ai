## Scenario 145: Kohl views a note list with mixed tagged and untagged notes

**GUID:** 01KRXXX5EYSQXB8M7T8022QXTK
**Severity:** silent-wrongness

**Setup:**

Kohl has saved three notes: 'Rust performance metrics' (tagged 'rust', 'performance'), 'Python async study' (tagged 'python'), and 'Random thought' (untagged). She navigates to the note list view.

**Trigger:**

The note list renders all three notes with their metadata.

**Expected:**

Each note displays its title, body preview, and tags as small badges below the preview. Tagged notes show their tag badges in a row; the untagged note shows no badges. All three notes are visually scannable and the tags are clearly distinct from the title/preview text.

**Concern:**

If tag rendering is missing or tag display is visually indistinguishable from the title, Kohl cannot use tags as a quick scanning hint. She loses the lightweight organization system that motivated adding tags in the first place.

**Property:**

Tag display in list view is a visual affordance that supports quick scanning and tag-based discovery.

**Implies:**
- Tags must render as distinct visual elements (badges or labels, not inline text).
- Untagged notes must not show empty badge areas (no visual clutter).
- Tags must be legible and scannable at list-view scale (small, but readable).
