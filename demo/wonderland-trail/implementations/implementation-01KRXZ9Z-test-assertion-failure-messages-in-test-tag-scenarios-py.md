## Implementation 053: Test assertion failure messages in test_tag_scenarios.py

**GUID:** 01KRXZ9Z9CT1RENJ7DN1P3GGRS
**Side:** backend
**Ticket:** ticket-01KRXZ5BMXQQT03839QCWRZH0M
**Contract:** test-assertions-have-failure-messages-for-debugging (per Caterpillar review and established test pattern)
**Ready for review:** yes

**Approach:**

Updated all assertions in test_tag_scenarios.py to include detailed failure messages using f-strings. Each message now clearly states the expected behavior, the actual result, and the context (e.g., response status, tag values, tag count). Follows the established pattern from test_notes_edge_cases.py for consistency.

**Schema Changes:**

none

**Files:**
- tests/test_tag_scenarios.py: added failure messages to assertions in test_tag_names_with_whitespace_only_entries, test_tag_names_case_sensitivity_deduplication, test_post_associate_tag_idempotence, test_delete_note_with_shared_tags_preserves_tag, test_post_associate_tag_with_whitespace_in_name, test_search_body_preview_with_emoji_truncation, test_concurrent_tag_creation_same_name_explicit_handling, test_put_and_delete_race_condition_sequence, test_search_body_preview_does_not_include_full_body, test_search_pagination_deterministic_ordering_on_tiebreak

**Known Limitations:**
- Test environment requires fastapi dependency installation; tests cannot be run in current env due to infrastructure gap
