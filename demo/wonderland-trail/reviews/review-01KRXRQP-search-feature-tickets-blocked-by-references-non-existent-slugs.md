## Review 003: Search feature tickets: blocked_by references non-existent slugs

**GUID:** 01KRXRQPTM82HTJCRVZM35A7X7
**Files reviewed:** .wonderland/tickets/ticket-01KRXRN4-backend-search-endpoint-for-notes-by-title-and-content.md, .wonderland/tickets/ticket-01KRXRN4-frontend-search-ui-component-and-results-display.md
**Verdict:** request-changes

### Findings

#### change-required: Backend search ticket blocked_by references non-existent slug: backend-note-schema-with-title-content-fields
**Location:** .wonderland/tickets/ticket-01KRXRN4-backend-search-endpoint-for-notes-by-title-and-content.md:12
**Quote:**

```
Blocked by: backend-note-schema-with-title-content-fields, backend-tag-system-schema-and-crud
```

**Read:** The backend search ticket lists two upstream dependencies, but the slug 'backend-note-schema-with-title-content-fields' does not appear on disk. The actual ticket is named 'backend-note-schema-with-create-read-endpoints'.
**Concern:** M7 implementations will not find the upstream ticket by this slug name. The dependency serialization will break, and Tweedledum may start work in the wrong order or duplicate it. Blocked_by must reference actual ticket slugs that exist on disk.
**Request:** Update blocked_by to reference the actual slug: 'backend-note-schema-with-create-read-endpoints' (ticket-01KRXRN7).

#### change-required: Backend search ticket blocked_by references non-existent slug: backend-tag-system-schema-and-crud
**Location:** .wonderland/tickets/ticket-01KRXRN4-backend-search-endpoint-for-notes-by-title-and-content.md:12
**Quote:**

```
Blocked by: backend-note-schema-with-title-content-fields, backend-tag-system-schema-and-crud
```

**Read:** The backend search ticket lists 'backend-tag-system-schema-and-crud' as a blocking dependency, but no such ticket exists on disk. The actual ticket is named 'backend-note-and-tag-crud-endpoints-with-schema'.
**Concern:** Same issue as above — the slug mismatch prevents M7 from reading the dependency graph correctly. The two search tickets will fail to deserialize their blocked_by references when M7 tries to build the implementation sequence.
**Request:** Update blocked_by to reference the actual slug: 'backend-note-and-tag-crud-endpoints-with-schema' (ticket-01KRXRNH).

#### change-required: Frontend search ticket blocked_by references non-existent ticket: frontend-note-detail-view-and-markdown-rendering
**Location:** .wonderland/tickets/ticket-01KRXRN4-frontend-search-ui-component-and-results-display.md:15
**Quote:**

```
Blocked by: backend-search-endpoint-for-notes-by-title-and-content, frontend-note-detail-view-and-markdown-rendering
```

**Read:** The frontend search ticket lists 'frontend-note-detail-view-and-markdown-rendering' as a blocking dependency. This ticket does not exist on disk. The codebase has 'frontend-markdown-preview-pane-with-live-rendering' (ticket-01KRXRNH) and 'frontend-editor-pane-with-title-input-markdown-body-editor-and-keystroke-buffer-to-localstorage' (ticket-01KRXRNH), but no separate 'note detail view' ticket.
**Concern:** The search acceptance criterion 'Clicking a result navigates to the note detail view' implies that view must exist before the search UI can be tested end-to-end. But the decomposition never captured 'display an existing note in a read-only view' as its own scope. Either the referenced ticket is missing (needs to be created), or the blocked_by is aspirational rather than naming actual upstream work.
**Request:** Clarify the intent: (1) If a separate read-only 'note detail view' ticket is truly needed, create it as a new ticket in M3.5. OR (2) If the detail view can be deferred (e.g., search results link to the editor in edit mode), remove this from blocked_by and add a note to the search ticket's Risk section explaining the deferral. The acceptance criterion 'Clicking a result navigates to the note detail view' must remain verifiable.

### Approvals

- The Rabbit correctly identified the dependency structure: search endpoint must be in place before search UI can integrate with it, and both foundation layer tickets (schema + tags, editor pane) are correctly blocking their respective downstream work. The intent behind the blocked_by assignments is sound.

### Cross-domain references

- This is a coordination/dependency issue, not a code issue. No cross-domain escalation needed; the Rabbit can resolve by correcting the ticket slugs and clarifying the note-detail-view scope.
