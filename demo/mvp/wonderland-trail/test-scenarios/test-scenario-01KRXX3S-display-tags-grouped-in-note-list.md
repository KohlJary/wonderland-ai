# Test Scenario: Display tags grouped in note list view

**Thread:** pipe.kohl-organizes-notes-with-optional-tags.tea-party-display-tags-grouped-in-note-list-view

**Ticket:** 034 (ticket-01KRXX3S)

---

## Scenario 1: Note with many tags renders all badges without layout overflow

**Severity:** degradation

**Setup:**
A note titled "Machine Learning Research" is tagged with 12 tags, several of which are 15+ characters long: ['deep-learning', 'pytorch', 'transformer-models', 'fine-tuning', 'transfer-learning', 'nlp', 'bert', 'evaluation-metrics', 'data-preprocessing', 'attention-mechanisms', 'hyperparameter-tuning', 'reproducibility'].

**Trigger:**
User performs a search that returns this note in the results list.

**Expected:**
All 12 tag badges are visible and readable in the note's tag section. Badges wrap across multiple lines if needed. The note's title and preview text remain fully visible above the tags. The total resultItem height stays under 400px.

**Concern:**
With many tags, especially long names, the flexbox wrapping should reflow them gracefully. But if the container is too narrow, badge text could overflow horizontally, long names could be truncated without warning, or the wrapping could create a very tall tag section that obscures other notes in the list. The CSS `flexWrap: 'wrap'` should handle this, but the actual rendering needs verification.

**Property:**
For all notes N with 8+ tags where some tags have names > 15 characters, all tag names render in full or with a clear ellipsis indicator, and the note item height is proportional to content, not excessively tall (< 500px).

**Implies:**
- Implies frontend layout concern: validate that resultTags flexbox wrapping is responsive and badges don't overflow. Flag for Tweedledee.

---

## Scenario 2: Note without tags renders cleanly with no empty tag section

**Severity:** degradation

**Setup:**
Three notes in search results: (1) "Untagged Daily Note" with no tags, (2) "Tagged Project" with 3 tags, (3) "Another Untagged" with no tags. User searches with an empty query to list all notes.

**Trigger:**
All three notes are visible in the results list at the same time.

**Expected:**
Untagged notes render without a tag section and appear visually balanced with tagged notes. The title and preview have consistent spacing and padding regardless of whether tags are present. No visual gap or reserved whitespace is left where tags would be.

**Concern:**
If the CSS always reserves vertical space for tags (e.g., `min-height` on the tag section), untagged notes would look misaligned. Or if the tag section renders as an empty div, there'd be unwanted whitespace. The code checks `note.tag_names.length > 0` before rendering, so this should work, but visual consistency needs verification.

**Property:**
For all notes N with tag_names.length == 0, the resultItem does not render a visible tag section and looks visually consistent with the overall list layout.

**Implies:**
(None — this is a visual verification test.)

---

## Scenario 3: Tag name containing emoji renders correctly without mojibake

**Severity:** curiosity

**Setup:**
A note is tagged with "🔬research", "🔗reference", and "📝draft".

**Trigger:**
The note appears in search results.

**Expected:**
Each emoji renders correctly adjacent to the text. The text is readable. No encoding corruption, replacement characters (U+FFFD), or mojibake.

**Concern:**
React handles unicode well in general, and the backend returns tag_names as plain strings, so this *should* work. But emoji rendering in small UI elements (pill badges) can have quirks in some browsers, especially with variable-width emoji or emoji with zero-width joiners. This is a curiosity test to verify the system handles unicode robustly.

**Property:**
For all tag names containing emoji, the rendered badge displays emoji + text without corruption or mojibake.

**Implies:**
(None — unicode robustness is a general property, not specific to this feature.)

---

## Scenario 4: Clicking a tag suggestion filters results; that tag moves from suggestions to selected chips

**Severity:** breakage

**Setup:**
A search query returns 3 notes: 2 are tagged "important", 1 is tagged "urgent", 1 has both. Below the search input, unselectedTags shows ["important", "urgent"]. selectedTags is empty.

**Trigger:**
User clicks the "important" tag suggestion button.

**Expected:**
selectedTags becomes ["important"]. The search re-runs with tags=["important"]. Results now show only notes with the "important" tag. The "important" tag disappears from the tag suggestions and appears as a blue chip in the selectedTags section above the suggestions.

**Concern:**
This is a core interaction of the Search UI. If handleAddTag doesn't properly update the selectedTags state, or if the useEffect doesn't re-run the search, the filter won't work. The unselectedTags computation must correctly exclude already-selected tags from the displayed suggestions. State management bugs here will cause the filter feature to silently fail.

**Property:**
For all unselected tags T, clicking T adds T to selectedTags and removes T from the displayed suggestions; the search immediately re-runs with the new tag filter applied.

**Implies:**
(None — state management is the Search component's responsibility.)

---

## Scenario 5: Removing a selected tag filter restores it to suggestions

**Severity:** breakage

**Setup:**
User has filtered by tags=["work", "urgent"], visible as two blue chips. Tag suggestions show remaining tags like "personal", "research".

**Trigger:**
User clicks the × button on the "work" chip to remove it.

**Expected:**
The "work" chip disappears. selectedTags becomes ["urgent"]. The search re-runs with tags=["urgent"]. Results update to show only notes with the "urgent" tag (or "urgent" + any other remaining selected tags). The "work" tag reappears in the tag suggestions below.

**Concern:**
The removeTag handler must correctly update selectedTags and trigger a new search. If it only removes the chip from the UI without updating the underlying state, subsequent searches will still filter by "work" in the background. This is a silent wrongness risk — the UI looks correct but the search is broken.

**Property:**
For all selected tags T, clicking the remove button on T's chip removes T from selectedTags and immediately re-runs the search with the remaining tags.

**Implies:**
(None — state management is the Search component's responsibility.)

---

## Scenario 6: Backend returns empty tag_names array; frontend handles without error

**Severity:** silent-wrongness

**Setup:**
Backend returns a SearchResultNote object with tag_names: [] and tag_ids: [].

**Trigger:**
renderNoteResult() is called for this note. The frontend checks `note.tag_names.length > 0` before rendering the tag section.

**Expected:**
No tag section is rendered. No error is thrown. The note displays title, preview, and date cleanly without a tag row.

**Concern:**
If tag_names is undefined instead of an empty array, the `.length` check would throw `TypeError: Cannot read property length of undefined`. While the backend should always return an array (per the contract), a defensive sanity check here ensures robustness. This is a silent-wrongness risk if the contract is broken: the UI could crash silently for users with notes that have no tags.

**Property:**
For all SearchResultNote objects returned by the search API, tag_names is guaranteed to be an array (possibly empty); the frontend's `.length` check never throws an error even if the backend returns tag_names as null or undefined.

**Implies:**
- Implies data-contract concern: verify the backend always includes tag_names as an array (never null/undefined) in search responses, even for notes with no tags. Flag for Tweedledum.

---

## Cross-Thread Summary

These scenarios validate:

1. **Visual resilience**: The UI handles dense tag loads and long tag names without breaking layout.
2. **Visual consistency**: The UI looks balanced whether notes are tagged or untagged.
3. **Unicode robustness**: The system handles emoji in tag names.
4. **State management**: Filtering by tags and removing filters both work correctly.
5. **Data contract**: The backend always returns properly-shaped responses.

All scenarios are grounded in the actual `Search.tsx` component code. High-severity scenarios (breakage) are about the filter feature working; degradation scenarios are about layout and visual stability.
