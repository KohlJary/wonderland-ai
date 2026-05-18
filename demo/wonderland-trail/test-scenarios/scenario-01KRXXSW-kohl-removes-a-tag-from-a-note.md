## Scenario 117: Kohl removes a tag from a note

**GUID:** 01KRXXSWWJHYATNJ080FHBB1TK
**Severity:** silent-wrongness

**Setup:**

A note has two tags: 'kinetics' and 'preliminary'. Kohl decides 'preliminary' no longer applies.

**Trigger:**

Kohl clicks the X button (or equivalent) on the 'preliminary' tag pill in the editor.

**Expected:**

The tag pill disappears from the UI immediately. On save, the association is persisted as removed. When Kohl re-opens the note or views the note list, 'preliminary' is gone and 'kinetics' remains.

**Concern:**

If removal fails silently, the tag will reappear on reload, confusing Kohl into thinking the UI is broken. If removal succeeds in the editor but the save fails, Kohl loses work.

**Property:**

Tag removal must be atomic with note save.
