## Review 004: Search feature tickets: blocked_by references invalid slugs

**GUID:** 01KRXS29R5DQ9DW6EB4N2Z2JXR
**Files reviewed:** .wonderland/tickets/ticket-01KRXRQZ-backend-search-endpoint-for-notes-by-title-and-content.md, .wonderland/tickets/ticket-01KRXRQZ-frontend-search-ui-component-and-results-display.md
**Verdict:** request-changes

### Findings

#### block: Search endpoint blocked_by references non-existent ticket slug
**Location:** ticket-01KRXRQZ-backend-search-endpoint.md:Dependencies
**Quote:**

```
Blocked by: foundation-schema-and-migrations, foundation-tag-system
```

**Read:** The search endpoint ticket declares dependencies on two upstream work items, but the slug names are abstract placeholders that don't resolve to actual ticket files in the .wonderland/tickets registry.
**Concern:** M7 implementations will receive a ticket with unresolved dependencies. When Tweedledum tries to start the search endpoint work, he cannot identify which tickets must ship first — he's blocked on placeholder names. This will either stall M7 or cause him to infer his own dependency chain, producing duplicate or divergent code.
**Request:** Replace 'foundation-schema-and-migrations' and 'foundation-tag-system' with the actual ticket slugs that define this work: 'backend-note-schema-definition-with-sqlite-migrations' (Ticket 010). That is the only required upstream blocker for the search endpoint — it needs the Note and Tag schema contract to exist before it can implement the search query logic.

#### block: Search UI blocked_by references partially non-existent ticket slug
**Location:** ticket-01KRXRQZ-frontend-search-ui.md:Dependencies
**Quote:**

```
Blocked by: backend-search-endpoint-for-notes-by-title-and-content, foundation-tag-system-ui-display
```

**Read:** The search UI ticket correctly identifies the search endpoint as a blocker (that slug exists), but also references 'foundation-tag-system-ui-display' which is an abstract placeholder with no corresponding ticket file.
**Concern:** Same as above — Tweedledee receives a partial dependency list. The real blocking work is Ticket 006 (backend-note-and-tag-crud-endpoints-with-schema), which includes both the tag schema AND the tag association endpoints that the UI calls. Without that ticket shipped, the search UI cannot wire tag filtering.
**Request:** Replace 'foundation-tag-system-ui-display' with 'backend-note-and-tag-crud-endpoints-with-schema' (Ticket 006). The search UI needs both the backend search endpoint (already correctly named) and the tag CRUD work (which defines the tag association contract the UI calls).

### Approvals

- Both search tickets are otherwise well-scoped: clear acceptance criteria, realistic estimates with confidence, and risk sections that acknowledge real concerns (pagination contract, tag list virtualization). The search endpoint's substring-match approach is appropriate for v1; the UI's pagination and tag filter affordances are well-grounded.

### Cross-domain references

- Dependency resolution here clears the path for M7 serialization. Once the blocked_by lists name actual ticket slugs, White Rabbit can finalize the ticket roster without concern.
