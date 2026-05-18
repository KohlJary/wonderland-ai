## Scenario 116: Kohl creates a tag that doesn't exist yet

**GUID:** 01KRXXSWWJHYATNJ080FHBB1TJ
**Severity:** degradation

**Setup:**

Kohl is tagging a note about a novel observation. None of the existing tags fit. The tag input field accepts free text.

**Trigger:**

Kohl types 'novel-metabolite' (a tag that doesn't exist), presses Enter or clicks Add.

**Expected:**

The system either (a) creates the tag on the fly and associates it to the note, or (b) shows a UI affordance (e.g., 'Create new tag: novel-metabolite?') so Kohl knows a new tag is being created. The tag then appears in the note's tag list and becomes available for future use.

**Concern:**

If the system silently fails to create new tags, Kohl is trapped: she can only use pre-existing tags, defeating the point of tagging. If creation works but is not visible, Kohl won't realize she can coin new tags.

**Property:**

Tag creation must be explicit or auto-complete, never silent.
