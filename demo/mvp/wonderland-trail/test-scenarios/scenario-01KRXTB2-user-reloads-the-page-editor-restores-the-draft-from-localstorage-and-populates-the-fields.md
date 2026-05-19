## Scenario 044: User reloads the page; editor restores the draft from localStorage and populates the fields

**GUID:** 01KRXTB2N1T8SKB4XW9T1D9EW2
**Severity:** breakage

**Setup:**

User has previously typed a draft ('My Experiment' / '# Results\n\nObserved precipitation.') into the editor. localStorage['noteDraft'] contains {title: 'My Experiment', body: '# Results\n\nObserved precipitation.'}. User reloads the page (F5).

**Trigger:**

Page reloads. EditorPane mounts.

**Expected:**

On mount, the component reads localStorage['noteDraft']. The title field is populated with 'My Experiment'. The body field is populated with '# Results\n\nObserved precipitation.'. The draft is visible and ready to edit.

**Concern:**

If restore on mount is not implemented, the draft will be lost and the user will see empty fields. This breaks the core promise of the feature.

**Property:**

For all drafts stored in localStorage['noteDraft'], the component's mount effect restores the exact stored content into the input fields before any user interaction.
