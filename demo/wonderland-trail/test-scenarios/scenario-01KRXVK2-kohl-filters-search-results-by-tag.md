## Scenario 108: Kohl filters search results by tag

**GUID:** 01KRXVK28H5RPDTG82TGG11W9R
**Severity:** degradation

**Setup:**

Kohl has notes tagged with 'experiment', 'reading', and 'reference'. She opens the search form and selects the 'experiment' tag checkbox (or multiselect).

**Trigger:**

Kohl types 'attention' while the 'experiment' tag filter is active.

**Expected:**

Results show only notes that (a) match the substring 'attention' AND (b) have the 'experiment' tag. Untagged notes or notes with other tags are excluded from the results.

**Concern:**

Without tag filtering, Kohl's search is polluted by notes in other contexts. If she's looking for a particular 'experiment' called 'attention', but she has reading notes with 'attention' in the title, she has to manually sift. Tag filtering makes the search useful for scoping her discovery.

**Property:**

tag filter AND logic (all selected tags must be present)
