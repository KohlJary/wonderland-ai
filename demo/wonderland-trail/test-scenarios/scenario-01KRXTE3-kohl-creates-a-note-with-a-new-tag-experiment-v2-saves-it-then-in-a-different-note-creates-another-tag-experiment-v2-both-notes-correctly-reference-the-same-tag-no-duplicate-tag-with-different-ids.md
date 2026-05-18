## Scenario 069: Kohl creates a note with a new tag 'experiment-v2', saves it, then in a different note creates another tag 'experiment-v2'; both notes correctly reference the same tag (no duplicate tag with different ids)

**GUID:** 01KRXTE35W88GEZR30A8W5VQ4H
**Severity:** silent-wrongness

**Setup:**

Database has no tags. Kohl is creating two notes sequentially

**Trigger:**

Note 1: title='First', tag_names=['experiment-v2'], Save. Note 2: title='Second', tag_names=['experiment-v2'], Save

**Expected:**

Both notes are created successfully. Both reference the same Tag record (e.g., tag_id=1, name='experiment-v2'). When Kohl searches by tag 'experiment-v2', both notes appear in results

**Concern:**

If the backend does not enforce tag name uniqueness, two notes might reference two different tag records with the same name. Searches for one tag might miss the other note. This is data duplication that breaks tag filtering

**Property:**

Tag names are globally unique; all notes with the same tag_name reference the same tag_id

**Implies:**
- Tag table has a UNIQUE constraint on name column
- Tag association code finds existing tag by name before creating a new one
