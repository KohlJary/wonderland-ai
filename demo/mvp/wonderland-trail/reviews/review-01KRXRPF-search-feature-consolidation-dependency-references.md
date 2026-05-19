## Review 001: Search feature consolidation: dependency references

**GUID:** 01KRXRPFFCDR9TX11VTZSD7TYD
**Files reviewed:** .wonderland/tickets/ticket-01KRXRN4-backend-search-endpoint-for-notes-by-title-and-content.md, .wonderland/tickets/ticket-01KRXRN4-frontend-search-ui-component-and-results-display.md
**Verdict:** request-changes

### Findings

#### change-required: Blocked-by reference uses story name instead of ticket slug
**Location:** ticket-01KRXRN4-backend-search-endpoint.md:15 and ticket-01KRXRN4-frontend-search-ui.md:15
**Quote:**

```
Blocked by: note-and-tag-schema-crud-endpoints
```

**Read:** Both search tickets declare a blocker on 'note-and-tag-schema-crud-endpoints', but this is a story/requirement identifier, not a ticket slug. The actual blocking tickets are on disk with slugs like 'ticket-01KRXRN7' and 'ticket-01KRXRNH'.
**Concern:** M7 implementations use Blocked by references to serialize dependencies. A reference that doesn't resolve to an actual ticket slug will cause confusion or prevent proper sequencing. The ticket files on disk are unambiguous; the blocker names must match them exactly.
**Request:** Correct both search tickets' 'Blocked by:' field to reference actual ticket slugs. The backend search endpoint should list ticket-01KRXRNH (note-and-tag CRUD) as its blocker. The frontend search UI should also list ticket-01KRXRNH (since response schema includes tags). Verify these resolve to actual files in .wonderland/tickets/.

### Approvals

- Scope separation is clean: backend endpoint handles query logic; frontend handles UI/UX. No overlap.
- Acceptance criteria are specific and testable for both tickets — estimates and confidence levels are realistic.
- Frontend ticket correctly identifies both a hard dependency (backend endpoint) and a soft dependency (the note schema foundations); this is good parallelization planning.
