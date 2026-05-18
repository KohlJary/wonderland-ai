## Review 002: Three tickets for 'Kohl can create and save notes' feature — consolidation review

**GUID:** 01KRXRQ6CC3NGRB3DDZ8BYC8BZ
**Files reviewed:** .wonderland/tickets/ticket-01KRXRN7-backend-note-schema-with-create-read-endpoints.md, .wonderland/tickets/ticket-01KRXRN7-frontend-note-editor-form-with-title-and-body-input.md, .wonderland/tickets/ticket-01KRXRN7-frontend-markdown-preview-renderer-component.md
**Verdict:** request-changes

### Findings

#### change-required: Backend ticket needs to be split per Operator ruling, and the schema ticket needs a clear contract definition acceptance criterion
**Location:** ticket-01KRXRN7-backend-note-schema-with-create-read-endpoints.md (entire)
**Quote:**

```
Implement SQLite schema for notes (id, title, body, created_at, updated_at) and REST endpoints for POST /notes (create) and GET /notes/:id (read).
```

**Read:** This ticket bundles two separable concerns: (1) defining the data shape/contract, and (2) implementing the HTTP endpoints that read/write that shape. The Operator ruled to split these so frontend design can proceed from a fixed contract while backend continues endpoint implementation.
**Concern:** If these stay bundled, the frontend engineer is blocked waiting for endpoints to exist, even though they only need the contract definition to design the form. Splitting creates parallelism.
**Request:** Create a new ticket 'Backend: Note schema contract definition' that owns (a) the SQLite schema definition, (b) a clear JSON contract for note shape {id, title, body, created_at, updated_at}, and (c) acceptance criteria that document the contract. Then reduce the existing 'endpoints' ticket to depend on that schema ticket. The frontend ticket can then list the schema contract ticket as 'Blocked by', not the endpoints ticket.

#### suggestion: Frontend form ticket should clarify what 'contract' it expects from backend before starting
**Location:** ticket-01KRXRN7-frontend-note-editor-form-with-title-and-body-input.md:Acceptance
**Quote:**

```
Wire POST to backend /notes endpoint on save button.
```

**Read:** The acceptance criterion names the endpoint, but doesn't document what shape the POST body should have or what shape the response returns. If the backend's endpoint shape changes during implementation, this ticket's acceptance could shift.
**Concern:** Acceptance criteria should be anchored to the contract, not to 'whatever the endpoint happens to return.' If the contract is separated (per the split), this ticket should reference it explicitly.
**Request:** Add to acceptance criteria: 'POST body matches contract {title, body}' and 'Response matches contract {id, title, body, created_at}'. This way the frontend engineer knows the exact shape they're designing for, and any deviation is a contract violation the Tweedles can catch early.

#### note: Markdown renderer ticket is well-scoped and independent
**Location:** ticket-01KRXRN7-frontend-markdown-preview-renderer-component.md
**Quote:**

```
Build a React component that accepts markdown string and renders HTML. Support headers, code blocks, lists, links, images, blockquotes.
```

**Read:** Clear scope, reasonable acceptance criteria, no blocking dependencies. The Hatter's scenarios will flesh out the markdown corner cases, but the ticket surface is solid.
**Concern:** No issues here.
**Request:** No changes needed.

### Approvals

- The three-ticket shape for this feature is right. Backend schema + endpoints, frontend form, frontend renderer — the stack span alignment is clean.
- Dependency modeling is sound: the schema unblocks the form, the form doesn't block the renderer. That's good parallelism.

### Cross-domain references

- The schema contract definition should be documented with enough precision that the Tweedles can negotiate it in their M3 Pair Protocol meeting without reopening it in M7. Rabbit, consider whether the 'schema ticket' (once split) should include a sample JSON contract in the ticket body, not just in the acceptance criteria.
