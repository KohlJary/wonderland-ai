## Scenario 157: Backend returns tag_names as null instead of empty array; frontend does not crash

**GUID:** 01KRXXXVW570ZA3859XC573SKD
**Severity:** silent-wrongness

**Setup:**

Backend bug (or regression): SearchResultNote returned from API has tag_names: null instead of tag_names: []. The frontend calls renderNoteResult() with this note.

**Trigger:**

renderNoteResult() checks `note.tag_names.length > 0` (line 134 of Search.tsx) to decide whether to render a tag section.

**Expected:**

The check does not throw a runtime error. If tag_names is null, the frontend gracefully handles it (either by treating it as an empty array or by an explicit null check) and renders the note without a tag section.

**Concern:**

If tag_names is null, the `.length` property access will throw `TypeError: Cannot read property 'length' of null`. This would crash the component and cause the entire search results view to fail. The contract specifies tag_names is always an array (possibly empty), but a defensive check here ensures robustness if the contract is broken.

**Property:**

For all SearchResultNote objects, accessing note.tag_names.length never throws an error, even if the backend violates the contract and returns null instead of an array.

**Implies:**
- Implies data-contract verification: confirm the backend search endpoint always returns tag_names as an array (never null/undefined) per contract-note-008. Flag for Tweedledum to verify the SearchResultNote response is always well-formed.
