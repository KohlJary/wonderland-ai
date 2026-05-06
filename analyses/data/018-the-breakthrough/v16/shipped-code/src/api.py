"""
Message storage API endpoint: POST /api/messages

Per contract-note-007: accepts (original_text, original_language, translated_text, 
target_language, message_retention_flag) and persists as a unit. Implements idempotence
(5-second deduplication window) and enforces invariants:
- original_text and original_language are immutable after creation
- (translation_status = 'complete') ⟺ (translated_text IS NOT NULL)
- message_id is returned to caller for subsequent queries

Blocking: UI (Tweedledee) calls this after translate service completes.
Unblocks: Tweedledee's message display; translate service integration
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.models import Message, TranslationStatus, LanguageCode, MessageDeduplicationWindow


# ============================================================================
# Request / Response Models
# ============================================================================

class CreateMessageRequest(BaseModel):
    """
    Request body for POST /api/messages
    
    Per contract-note-007: frontend passes (original_text, original_language, 
    translated_text, target_language). Backend determines translation_status
    based on whether translated_text is provided.
    """
    original_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Original message text in source language"
    )
    original_language: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Source language code (EN, DE, JA, ...)"
    )
    translated_text: Optional[str] = Field(
        None,
        max_length=2000,
        description="Translated text (optional); if provided, translation_status=complete"
    )
    target_language: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Target language code; required if translated_text is provided"
    )
    message_retention_flag: Optional[str] = Field(
        None,
        max_length=100,
        description="GDPR retention policy (per Sophie's story)"
    )
    
    @field_validator('original_language', 'target_language', mode='before')
    @classmethod
    def validate_language_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate language code is in supported list."""
        if v is None:
            return v
        if v not in [lang.value for lang in LanguageCode]:
            raise ValueError(f"Unsupported language code: {v}")
        return v
    
    @field_validator('translated_text', mode='before')
    @classmethod
    def validate_translated_text_requires_target(cls, v: Optional[str], info) -> Optional[str]:
        """If translated_text is provided, target_language must be provided."""
        if v is not None and not info.data.get('target_language'):
            raise ValueError("target_language is required when translated_text is provided")
        return v


class MessageResponse(BaseModel):
    """
    Response body for POST /api/messages
    
    Per contract-note-007: returns full message record with generated message_id
    and computed translation_status.
    """
    message_id: UUID
    sender_id: UUID
    original_text: str
    original_language: str
    translated_text: Optional[str]
    target_language: Optional[str]
    translation_model: Optional[str]
    translation_status: str  # 'pending' | 'complete' | 'failed'
    translation_timestamp: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Endpoint Implementation
# ============================================================================

def create_message_endpoint(
    sender_id: UUID,
    request: CreateMessageRequest,
    db: Session
) -> MessageResponse:
    """
    Create a new message or return dedup'd message if within 5-second window.
    
    Workflow per contract-note-007:
    1. Check for duplicate within 5-second window
    2. If found, return existing message_id + current record state
    3. If not found:
       a. If translated_text is provided: set translation_status='complete'
       b. If translated_text is None: set translation_status='pending'
       c. Persist message record
       d. Return full record with message_id
    
    Invariants enforced:
    - original_text and original_language are immutable
    - (translation_status = 'complete') ⟺ (translated_text IS NOT NULL)
    - message_retention_flag is stored for GDPR compliance
    
    Args:
        sender_id: UUID of message author
        request: CreateMessageRequest with original_text, original_language, etc.
        db: SQLAlchemy session
    
    Returns:
        MessageResponse with message_id and full record
    
    Raises:
        HTTPException 400: validation error (language unsupported, text too long, etc.)
    """
    
    # Check deduplication window
    duplicate = MessageDeduplicationWindow.find_duplicate(
        sender_id=sender_id,
        original_text=request.original_text,
        original_language=request.original_language,
        target_language=request.target_language,
        session=db
    )
    
    if duplicate:
        return MessageResponse.from_attributes(duplicate)
    
    # Determine translation_status based on whether translated_text is provided
    if request.translated_text is not None:
        translation_status = TranslationStatus.COMPLETE.value
        translation_timestamp = datetime.utcnow()
        translation_model = "claude-haiku-4.5"  # Default model for v1
    else:
        translation_status = TranslationStatus.PENDING.value
        translation_timestamp = None
        translation_model = None
    
    # Create message record
    message = Message(
        sender_id=sender_id,
        original_text=request.original_text,
        original_language=request.original_language,
        translated_text=request.translated_text,
        target_language=request.target_language,
        translation_model=translation_model,
        translation_timestamp=translation_timestamp,
        translation_status=translation_status,
        message_retention_flag=request.message_retention_flag,
    )
    
    # Persist
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return MessageResponse.from_attributes(message)


# ============================================================================
# Retrieval Endpoints (support for Tweedledee's read path)
# ============================================================================

def get_message(
    message_id: UUID,
    sender_id: UUID,
    db: Session
) -> MessageResponse:
    """
    Retrieve a message by message_id.
    
    Per contract-note-003/008: frontend displays original + translation together
    (with toggle to hide original). This endpoint returns full record including
    both original_text and translated_text (if translation_status='complete').
    
    Args:
        message_id: UUID of message to retrieve
        sender_id: UUID of requesting user (for authorization)
        db: SQLAlchemy session
    
    Returns:
        MessageResponse with full message record
    
    Raises:
        HTTPException 404: message not found
        HTTPException 403: sender_id does not match message author
    """
    message = db.query(Message).filter(Message.message_id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found"
        )
    
    # Note: authorization (sender_id check) is placeholder; actual auth handled by middleware
    if message.sender_id != sender_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this message"
        )
    
    return MessageResponse.from_attributes(message)


def list_messages(
    sender_id: UUID,
    db: Session,
    limit: int = 50,
    offset: int = 0
) -> list[MessageResponse]:
    """
    List messages for a sender, ordered by creation time (descending).
    
    Per contract-note-003: frontend requests message list for display.
    This endpoint returns messages in reverse chronological order (newest first).
    
    Args:
        sender_id: UUID of message author
        db: SQLAlchemy session
        limit: max number of messages to return (default 50, max 500)
        offset: pagination offset
    
    Returns:
        List of MessageResponse objects
    """
    limit = min(limit, 500)  # Cap at 500
    
    messages = (
        db.query(Message)
        .filter(Message.sender_id == sender_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return [MessageResponse.from_attributes(m) for m in messages]
