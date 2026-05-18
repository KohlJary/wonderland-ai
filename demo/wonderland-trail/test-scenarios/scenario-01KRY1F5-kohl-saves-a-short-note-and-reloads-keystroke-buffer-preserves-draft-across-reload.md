## Scenario 359: Kohl saves a short note and reloads; keystroke buffer preserves draft across reload

**GUID:** 01KRY1F5JJWC63TXB9SQCCBZWE
**Severity:** silent-wrongness

**Setup:**

Kohl has typed 'Research findings from Q4' into the title field and 'Observed pattern X in dataset Y' into the body. She has not clicked Save yet. The browser tab has been open for 3 minutes. Her keystroke buffer in localStorage contains the current draft state.

**Trigger:**

Kohl accidentally closes the tab (or the browser crashes). She reopens the app and navigates back to /editor. The app checks localStorage for unsaved drafts.

**Expected:**

On app boot, the editor finds the localStorage entry for this note draft and displays it: title 'Research findings from Q4', body 'Observed pattern X in dataset Y'. The user sees her work exactly as she left it. A 'Restore Draft' button or auto-restore message confirms the recovery.

**Concern:**

If localStorage persistence is broken or the keystroke buffer fails to capture changes, Kohl loses her work on page reload. This is the core resilience promise of the keystroke buffering feature. Silent wrongness because the app might load successfully, but her draft is gone without warning.

**Property:**

keystroke buffer survival across page reload
