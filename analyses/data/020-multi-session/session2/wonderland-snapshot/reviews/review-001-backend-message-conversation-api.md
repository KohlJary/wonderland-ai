## Review 001: Backend message + conversation API

**Files reviewed:** src/backend/api/messages.py, src/backend/api/users.py, src/backend/models.py, src/backend/api/__init__.py
**Verdict:** request-changes

### Findings

#### block: Import order violation: `or_` imported at module end, used mid-file
**Location:** src/backend/api/messages.py:161-167
**Quote:**

```
existing = (
        db.query(Conversation)
        .filter(
            or_(
                and_(Conversation.user1_id == payload.user1_id, Conversation.user2_id == payload.user2_id),
                and_(Conversation.user1_id == payload.user2_id, Conversation.user2_id == payload.user1_id),
            )
```

**Read:** The `or_` function is used in `create_conversation` at line 161, but the import statement `from sqlalchemy import or_` appears at the end of the file (line 381), after all function definitions. This will cause a NameError at runtime.
**Concern:** This is a correctness bug. The import must appear at the top of the module, before any use. The current structure makes the code uninspectable — a reader scanning imports misses this dependency, and the import at the end is dead code that should not be there.
**Request:** Move `from sqlalchemy import or_` to the top imports section (around line 20 where `and_` is already imported). Remove the duplicate import at line 381.

#### change-required: Code duplication between messages.py and users.py
**Location:** src/backend/api/messages.py:34-95 vs src/backend/api/users.py:21-49
**Quote:**

```
In messages.py:
class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    language_preference: str = Field(min_length=2, max_length=5)

class UserResponse(BaseModel):
    id: int
    username: str
    language_preference: str
    created_at: str

class ConversationCreate(BaseModel):
    user1_id: int
    user2_id: int

class ConversationResponse(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: str
```

**Read:** UserCreate, UserResponse, ConversationCreate, ConversationResponse are defined identically in both messages.py (lines 34-95) and users.py (lines 21-49). They are also used in users.py endpoints. The duplication creates a maintenance burden: if a contract change is needed, it must be made in both places or the definitions will diverge.
**Concern:** Schema duplication violates DRY. If a developer modifies UserResponse in one file and forgets the other, the two modules will have inconsistent contracts. More specifically: messages.py imports these but also defines them, creating ambiguity about which is canonical. The file that owns the endpoint (users.py) should own the schemas.
**Request:** Define UserCreate, UserResponse, ConversationCreate, ConversationResponse in users.py only (they already exist there). In messages.py, remove the duplicate definitions and import them from users: `from src.backend.api.users import UserCreate, UserResponse, ConversationCreate, ConversationResponse`.

#### change-required: Redundant user/conversation endpoints in messages.py
**Location:** src/backend/api/messages.py:103-231
**Quote:**

```
@router.post("/users", response_model=UserResponse)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    ...

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserResponse:
    ...

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(...) -> ConversationResponse:
    ...

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)) -> ConversationResponse:
    ...
```

**Read:** The create_user, get_user, create_conversation, get_conversation endpoints are implemented in messages.py (lines 103-231), but they are already implemented identically in users.py (lines 51-137). Both routers are mounted under the same prefix `/api` in __init__.py. This creates duplicate endpoints and undefined behavior about which route handler will be called.
**Concern:** Having the same endpoint defined in two places is a correctness bug. When both routers are registered with the same prefix, FastAPI's behavior is unspecified; the last one mounted wins, or there's a collision. This will confuse future readers about where user/conversation logic lives. Additionally, messages.py should be about *messages*, not about users and conversations.
**Request:** Remove the user and conversation endpoints from messages.py (lines 103-231). Keep only the message-specific endpoints: list_messages, create_message, mark_message_translated, mark_message_translation_failed. User and conversation management belongs in users.py.

#### suggestion: Unnecessary imports in messages.py after deduplication
**Location:** src/backend/api/messages.py:1-22
**Quote:**

```
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import Conversation, Message, TranslationStatus, User
```

**Read:** After removing the user/conversation endpoints, several imports become unused. Specifically: `BaseModel` and `Field` (no longer defining UserCreate, UserResponse, etc.), `Conversation` and `User` (no longer querying for them in removed functions).
**Concern:** Unused imports clutter the namespace and make it harder for the next reader to understand what this module actually does. 'If it's imported, it's used' is a mental shortcut that fails when dead imports remain.
**Request:** After removing the user/conversation endpoints, prune the imports: remove `BaseModel, Field` (message schemas remain and are simple enough to inline or keep), remove imports of `Conversation` and `User` if they're no longer needed. Keep only imports for Message and TranslationStatus, which are central to this module.

#### note: Message creation correctly respects contracts
**Location:** src/backend/api/messages.py:250-319
**Quote:**

```
msg = Message(
        conversation_id=conversation_id,
        sender_id=payload.sender_id,
        original_text=payload.original_text,
        translated_text=None,
        language_pair=language_pair,
        translation_status=TranslationStatus.PENDING_TRANSLATION,
        created_at=datetime.now(timezone.utc),
        translated_at=None,
        error_code=None,
        error_message=None,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
```

**Read:** Message creation initializes all required fields per contract-note-001. language_pair is computed from sender's language to receiver's language (immutable). translation_status is set to PENDING_TRANSLATION. translated_text and translated_at are null (optimistic render). The response is properly serialized via to_dict().
**Concern:** None — this is correct.
**Request:** None.

#### note: Polling endpoint respects contract and ordering
**Location:** src/backend/api/messages.py:234-248
**Quote:**

```
@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(conversation_id: int, db: Session = Depends(get_db)) -> list[MessageResponse]:
    ...
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )

    return [MessageResponse(**msg.to_dict()) for msg in messages]
```

**Read:** The polling endpoint returns all messages for a conversation, ordered by created_at ascending (oldest first). This matches the contract-note-006 polling contract. The conversation existence check is enforced. All messages are serialized with their translation_status fields intact.
**Concern:** None — this is correct.
**Request:** None.

#### note: Translation worker endpoints are internal, correctly scoped
**Location:** src/backend/api/messages.py:323-377
**Quote:**

```
@router.post("/messages/{message_id}/translate", response_model=MessageResponse)
def mark_message_translated(...)

@router.post("/messages/{message_id}/translate-failed", response_model=MessageResponse)
def mark_message_translation_failed(...)
```

**Read:** Two internal endpoints for the translation worker to call: mark_message_translated and mark_message_translation_failed. Both enforce the invariant that the message must be in PENDING_TRANSLATION state before transitioning. Timestamps are set correctly (translated_at when success, None on error). Error context is populated on failure.
**Concern:** None — these are correctly implemented. (Note: they're not exposed in users.py, so they won't be duplicated.)
**Request:** None.

### Approvals

- The message envelope contract (contract-note-001) is fully realized: all required fields are present, immutability of language_pair is enforced at creation, translation_status state machine is correctly implemented.
- The optimistic render timing (contract-note-007) is correct: messages appear immediately with status=pending_translation, translated_text null until translation completes.
- The language display contract (contract-note-004) is correctly implemented: language_pair is computed as sender_language->receiver_language.
- Error handling is thorough: all endpoints validate preconditions and return appropriate 400/404 responses with clear messages.
- Test coverage is comprehensive and aligned with the contracts: optimistic render, polling, language pairs, validation.

### Cross-domain references

- After deduplication, messages.py will have no user/conversation logic, which is correct — those endpoints belong entirely in users.py.
- No architectural issues identified.
- Test coverage is sufficient; no gaps found.
