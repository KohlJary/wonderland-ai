## Scenario 299: User opens the same editor in two tabs simultaneously and types in both; second tab's keystroke overwrites first tab's work without warning

**GUID:** 01KRY1ARRE8QYC9GT63D0YD5GY
**Severity:** silent-wrongness

**Setup:**

Two browser tabs both open http://localhost:3000 and load the editor. Tab A shows editor with title='Rust async'. Tab B shows editor with title='' (blank). Both tabs share the same localStorage key 'editor_draft'.

**Trigger:**

User types 'patterns' into title in Tab A (resulting in title='Rust async patterns'). localStorage now contains {title: 'Rust async patterns', ...}. User switches to Tab B and types 'Python GIL' into title. localStorage is updated to {title: 'Python GIL', ...}, overwriting Tab A's work.

**Expected:**

One of two options: (a) Tab A detects that another tab has modified localStorage and displays a warning: 'This note was edited in another tab. Your changes may be lost. Refresh to sync?' Or (b) the editor uses a revision ID or timestamp to detect conflicts and merges (later-stage feature). Or (c) the story explicitly accepts this risk as a known limitation of the single-device-single-user model.

**Concern:**

Kohl opens the editor in two tabs while researching. She types an idea in Tab A, switches to Tab B, types another idea, then goes back to Tab A and hits Save. The first idea is gone — silently overwritten by Tab B. She loses work without warning.

**Property:**

When multiple tabs have the editor open and both are modifying the same localStorage key, the user must be notified of the conflict, or the system must prevent concurrent edits.

**Implies:**
- Implies architectural decision: should the editor detect and warn about multi-tab conflicts? Story flags single-user scope, but this is a real-world footgun that users will hit.
- Implies: later story about multi-tab coordination or revision ID collision detection.
