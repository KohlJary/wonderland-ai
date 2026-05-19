## Contract Note 019: Tag name normalization and validation semantics

**GUID:** 01KRXYD0MKXJHKX27JY3P4NKHP
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

contract-note-005 (Tag Creation vs. Lookup vs. Auto-Create) specifies auto-create-by-name but leaves validation unspecified. Implementation in notes.py auto-creates tags without normalization (stores whitespace as-is). Frontend has no validation rules yet (Tweedledee is blocked waiting for contract).

**Proposed Change:**

Lock binding contract: tag names must be stripped of leading/trailing whitespace on both client and server. Validation rules: (1) after stripping, tag name must be 1-100 characters; (2) tag name cannot be empty string or whitespace-only; (3) duplicate tag names within a single note are deduplicated (case-sensitive, so 'Research' and 'research' are distinct tags); (4) tag names are stored normalized (stripped). Request validation happens client-side (reject user input before sending); server-side validation rejects request (400 Bad Request) if incoming tag_names violate these rules. Response returns normalized tag_names so client can update UI with canonical form.

**Source:** Tweedledee's blocking question on tag validation semantics + Hatter's test scenarios (test_post_notes_with_tag_names_containing_whitespace_only_entries, test_post_notes_with_tag_names_research_research_research_case_sensitivity_deduplication). Contract-note-005 left this unspecified; feature cannot ship until both Tweedles agree on the boundary.

**Frontend Impact (Tweedledee):**

(Tweedledee to confirm) Client-side validation mirrors backend rules: (1) Strip leading/trailing whitespace from user input before displaying or sending. Show the normalized form in the chip. (2) Reject (don't add the chip) if input after stripping is empty. Provide user feedback: 'Tag cannot be empty or whitespace only'. (3) Reject duplicate tag names before sending: if user tries to add 'research' and 'research' is already a chip, show feedback 'Tag already added'. (4) Treat case-sensitive: 'research' and 'Research' are allowed as distinct tags if user explicitly types both. This lets power users organize by case if they want.

**Backend Impact (Tweedledum):**

Backend enforces: (1) Strip leading/trailing whitespace from all tag_names on input before validation or database write. (2) Reject (400 Bad Request) any tag_name that after stripping is empty string or whitespace-only. (3) Deduplicate tag_names within a single request (case-sensitive: 'research' and 'Research' are distinct, but ['research', 'research'] deduplicate to ['research']). (4) Store tag names in normalized form (whitespace-stripped). (5) Case-sensitive: do NOT normalize case. 'research', 'Research', 'RESEARCH' are three separate tags if used in the system, but within a single note, deduplicate by value (so if user sends ['research', 'research', 'RESEARCH'], you store ['research', 'RESEARCH'] — two tags).
