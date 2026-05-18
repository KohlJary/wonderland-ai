## Scenario 330: Audit trail JSON serialization handles unicode, emoji, special characters

**GUID:** 01KRY1CT9RYR088A6WTPTNAHTC
**Severity:** silent-wrongness

**Setup:**

Kohl saves a note with title "🚀 Attention mechanisms", body "Query weights: ∑ softmax(Q·K^T) where K = [k₁, k₂, k₃]", tags ["résumé", "naïve-bayes"].

**Trigger:**

The save endpoint serializes the saved_state to JSON and stores it in audit_log.

**Expected:**

The audit_log entry contains valid JSON that preserves all characters. Later, parsing the JSON yields the exact original text. No mojibake, no replacement characters, no truncation.

**Concern:**

JSON serialization might escape unicode incorrectly, lose diacritics, truncate emoji, use an encoding that doesn't round-trip, or fail entirely on special characters. The audit trail becomes unreadable for non-ASCII content.

**Property:**

For all note states S containing any valid Unicode characters (emoji, combining marks, math symbols, accented letters), the audit_log entry's saved_state is valid JSON that, when deserialized, yields the exact original characters.

**Implies:**
- JSON serialization must use UTF-8 encoding consistently
- The database must be configured for UTF-8
- Forensic queries should round-trip: serialize, deserialize, compare to original
