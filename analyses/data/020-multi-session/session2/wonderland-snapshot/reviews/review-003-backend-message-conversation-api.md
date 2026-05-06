## Review 003: Backend message + conversation API

**Files reviewed:** src/backend/api/messages.py, src/backend/api/schemas.py, src/backend/api/users.py, src/backend/models.py
**Verdict:** request-changes

### Findings

#### change-required: Schema duplication between messages.py and schemas.py
**Location:** src/backend/api/messages.py:34-106 and src/backend/api/schemas.py:13-79
**Quote:**

```
UserCreate, UserResponse, ConversationCreate, ConversationResponse, MessageCreate, MessageResponse are defined identically in both files.
```

**Read:** The same Pydantic schema classes are defined in two places. When contracts evolve, both files must stay in sync or they will diverge silently.
**Concern:** This creates a maintenance hazard and violates DRY. The second copy in messages.py shadows the canonical definitions in schemas.py, making it unclear which is the source of truth.
**Request:** Delete the schema definitions from messages.py (lines 34-106) and import them from schemas.py instead: `from src.backend.api.schemas import UserCreate, UserResponse, ConversationCreate, ConversationResponse, MessageCreate, MessageResponse`. schemas.py becomes the single source of truth for all request/response models.

#### change-required: Route collision: users.py re-exports messages.py router
**Location:** src/backend/api/users.py:1-30
**Quote:**

```
from src.backend.api.messages import (
    ConversationCreate,
    ...
    router,
)

__all__ = [
    "router",
    ...
]
```

**Read:** users.py imports and re-exports the router object from messages.py. When api/__init__.py includes both routers (if it were to), they would collide because both define the same endpoints at the same path. Currently only messages_router is included, so collisions don't manifest yet, but the code structure creates the hazard.
**Concern:** This pattern invites a future developer to `include_router(users_router)` thinking users.py is the canonical user/conversation endpoint location, which would cause silent endpoint overwrites or inconsistent behavior. The comment admits this is a re-export for 'backwards compatibility' — but there is no prior art to maintain backwards compatibility with.
**Request:** Delete users.py entirely. All user, conversation, and message endpoints live in messages.py; api/__init__.py includes only messages_router. If endpoint organization becomes a concern later, refactor into separate route files with distinct endpoint prefixes or distinct concerns — but do not maintain a shadow re-export module that creates collision hazards.

#### suggestion: Import ordering: or_() used before import statement
**Location:** src/backend/api/messages.py:18 vs line ~261 (approximate, need full file)
**Quote:**

```
Line 18: `from sqlalchemy import and_, or_`
Line 261: `or_(
                and_(Conversation.user1_id == payload.user1_id, Conversation.user2_id == payload.user2_id),
                and_(Conversation.user1_id == payload.user2_id, Conversation.user2_id == payload.user1_id),
            )`
```

**Read:** The import `from sqlalchemy import and_, or_` appears at the top of the file (line 18), and `or_()` is used later in the `create_conversation()` function. Python resolves this correctly because imports are processed before function bodies execute.
**Concern:** While this works at runtime, the earlier statement in my concern said 'import statement appears at the very end of the file' — checking the diff, imports are actually at the top. This is correct. No action needed on this point; the previous concern was based on incomplete diff reading.
**Request:** No change required. Imports are correctly ordered at the top of the file.

### Approvals

- The data model is well-designed: TranslationStatus enum correctly constrains the state machine, nullable columns align with status (translated_text is null iff pending_translation, error fields are null iff not failed). This prevents state inconsistency at the DB layer.
- The Message.to_dict() method correctly implements the contract-note-001 (message envelope) requirement that translated_text is always a string (empty string when null) — this prevents frontend null-handling bugs.
- The conversation deduplication logic is solid: the `or_()` check on lines 261–266 correctly handles both (user1, user2) and (user2, user1) as the same conversation. Unique constraint reinforces this at the DB layer.
- Test coverage is comprehensive and well-named: test_create_message_optimistic_render, test_language_pair_contract, test_list_messages_polling_contract all verify the locked contracts directly. Tests validate both happy paths and error boundaries (sender not in conversation, nonexistent users, empty text).
- Error handling on API endpoints is specific and actionable: each HTTPException names what is wrong (e.g., 'Sender is not a member of this conversation' rather than generic 'Bad Request'). Callers (frontend) can distinguish whether they need to retry, redirect, or show an error to the user.

### Cross-domain references

- Tweedledee needs to know that users.py will be deleted — confirm the frontend is not importing from that path.
- Contract notes 001–008 are still referenced in code comments but not yet formalized as versioned artifacts. Tweedledum flagged this; waiting for explicit contract note artifacts before frontend can implement against durable contracts.
