## Review 004: Backend block/unblock state machine and API

**Files reviewed:** src/backend/api/messages.py, src/backend/models.py
**Verdict:** request-changes

### Findings

#### change-required: Schema duplication recurrence: BlockedUser fields defined in both users.py and messages.py
**Location:** src/backend/api/messages.py:115-125
**Quote:**

```
class BlockedUser(BaseModel):
    user_id: int
    blocked_by_id: int
    blocked_at: datetime
    reason: Optional[str]
```

**Read:** BlockedUser is the API response schema for blocked user metadata. This same schema appears identically in src/backend/api/users.py (line 87-97).
**Concern:** This mirrors the schema duplication pattern flagged in review-002. When the blocking contract evolves — e.g., adding an `unblock_reason` field or changing `blocked_at` semantics — both files must be kept in sync. Divergence is inevitable and will cause silent contract violations at the boundary.
**Request:** Move BlockedUser to a shared schemas module (e.g., src/backend/api/schemas.py, which should also contain UserCreate, UserResponse, ConversationCreate, ConversationResponse from session 1's findings). Import it in both users.py and messages.py. This is the same refactor recommended in review-002; blocking this feature on the schema consolidation ensures it doesn't compound the maintenance debt.

#### change-required: Route collision recurrence: POST /conversations/{id}/block and /messages/{id}/block defined in both files
**Location:** src/backend/api/messages.py:210-230
**Quote:**

```
@router.post('/conversations/{id}/block')
def block_conversation(id: int, reason: str): ...

@router.post('/messages/{id}/block')
def block_message(id: int, reason: str): ...
```

**Read:** The blocking endpoints are mounted on the messages router. However, a parallel set of blocking endpoints is already defined in src/backend/api/users.py (lines 180-200), and both routers are included in main.py with the same /api prefix. The second router's endpoints will overwrite the first.
**Concern:** This mirrors the route collision pattern flagged in review-002. The endpoints will silently overwrite at runtime, and the wrong handler may execute depending on import order. For blocking, this is a correctness hazard — a request to block a conversation might execute the message-block logic instead, or vice versa, leaving the conversation unblocked.
**Request:** Consolidate blocking endpoints in a single router. The semantic choice is: do blocking operations belong in the users API (because they're about user relationships) or in the messages API (because they're about message/conversation visibility)? Route all blocking endpoints through one place, and include that router once in main.py. This is the same refactor recommended in review-002.

#### suggestion: Import ordering: `or_()` imported at line 381, first used at line 167
**Location:** src/backend/api/messages.py:167 and 381
**Quote:**

```
Line 167: return db.query(Message).filter(or_(Message.blocked_by_id == user_id, ...)).all()
Line 381: from sqlalchemy import or_
```

**Read:** The `or_()` operator is used in the `get_blocked_messages()` function but imported at the end of the file. Python resolves all imports before executing function bodies, so the code runs correctly.
**Concern:** This repeats the import-ordering anti-pattern flagged in review-002. While it works at runtime, it violates Python convention and creates a readability trap — a maintainer scanning the top of the file won't see the import, and a maintainer adding a new function using `or_()` might assume it's not imported and add a duplicate. The convention note from session 1 should make this non-negotiable going forward.
**Request:** Move the import to the top of the file with the other sqlalchemy imports (around line 1-5). This is low-risk and clears the anti-pattern.

### Approvals

- The block/unblock state machine correctly models immutability (once blocked, can only unblock). The database invariant `UNIQUE(conversation_id, blocking_user_id)` prevents duplicate blocks and is enforced at the schema level — well done.
- The null semantics for `unblock_reason` when status is BLOCKED (must be null) are enforced in the response schema validation. This is precise contract-level thinking.
- The error handling on block attempts when already blocked (status 409 Conflict) is the right recovery path and properly propagates context.

### Cross-domain references

- Schema consolidation and route collision are implementation-clarity issues, not architectural ones, so no Cat handoff needed.
- The blocking state machine itself is sound — no test gaps implied for the Hatter beyond what polling tests should already cover.
