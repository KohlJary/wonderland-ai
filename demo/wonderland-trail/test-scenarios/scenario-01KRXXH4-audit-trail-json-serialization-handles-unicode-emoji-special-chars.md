## Scenario: Audit trail JSON serialization handles unicode, emoji, special characters

**Severity:** silent-wrongness

**Setup:**
Kohl saves a note with:
- title: "🚀 Attention mechanisms"
- body: "Query weights: ∑ softmax(Q·K^T) where K = [k₁, k₂, k₃]"
- tags: ["résumé", "naïve-bayes"]

**Trigger:**
The save endpoint writes to the notes table and audit_log. The saved_state JSON is serialized and stored.

**Expected:**
The audit_log entry's saved_state field contains valid JSON that preserves all characters:
```json
{
  "title": "🚀 Attention mechanisms",
  "body": "Query weights: ∑ softmax(Q·K^T) where K = [k₁, k₂, k₃]",
  "tag_names": ["résumé", "naïve-bayes"],
  ...
}
```

Later, when the forensic query retrieves this entry, parsing the JSON and reading the characters yields the exact original text. No mojibake, no replacement characters, no truncation.

**Concern:**
JSON serialization might:
- Escape unicode characters incorrectly (e.g., \uXXXX sequences that don't round-trip)
- Lose combining characters or diacritics (é → e)
- Truncate emoji or grapheme clusters (🚀 → incomplete byte sequence)
- Use an encoding that doesn't round-trip (e.g., UTF-8 to Latin-1 and back)
- Fail entirely on special characters (raise an exception, leaving the audit entry incomplete or missing)

If this happens, the audit trail is unreadable for notes with non-ASCII content. Kohl's international or emoji-heavy notes cannot be forensically reconstructed because the audit trail is corrupted.

**Property:**
For all note states S containing any valid Unicode characters (including emoji, combining marks, math symbols, accented letters), the audit_log entry's saved_state is valid JSON that, when deserialized, yields the exact original characters and strings. No data is lost or mangled in serialization/deserialization.

**Implies:**
- JSON serialization must use UTF-8 encoding consistently
- Python's json module (or equivalent) should handle Unicode correctly by default, but edge cases with combining characters or rare emoji should be tested
- The database must be configured for UTF-8 (SQLite default is fine; Postgres requires explicit setting)
- Forensic queries should round-trip: serialize, deserialize, compare to original
