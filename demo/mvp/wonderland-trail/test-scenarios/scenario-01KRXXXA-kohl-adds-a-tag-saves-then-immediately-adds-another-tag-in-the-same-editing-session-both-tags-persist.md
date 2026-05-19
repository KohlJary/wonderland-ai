## Scenario 152: Kohl adds a tag, saves, then immediately adds another tag in the same editing session; both tags persist

**GUID:** 01KRXXXAWK63FBTGKJSS5NBRY4
**Severity:** silent-wrongness

**Setup:**

Kohl saves a note with tag 'rust'. The note reloads and displays the 'rust' tag. She is still in the editor. She types a new tag 'concurrency' into the tag input.

**Trigger:**

Kohl presses Enter to add 'concurrency' (it appears as a chip), then immediately clicks Save without any other edits.

**Expected:**

Both 'rust' and 'concurrency' are sent to the backend in the save request. After save completes, the note displays both tags. No error message appears.

**Concern:**

If the second tag is added to the local state but not included in the save payload (e.g., the tag_names array is stale or the component state is not flushed before serializing the request), the tag will be lost from the backend. On reload, only 'rust' is present.

**Property:**

Each save sends the complete, current tag list; no tag is ever orphaned by stale state serialization.

**Implies:**
- The tag_names state must be flushed into the save payload at the moment Save is clicked, not at an earlier point.
- The tag input state and the Editor's tag state must be synchronized before the save request is constructed.
