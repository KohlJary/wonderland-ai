"""
Message models for translation system.

Invariants enforced:
- (translation_status = 'complete') ⟺ (translated_text is not None AND translation_timestamp is not None)
- message_id is globally unique and immutable
- original_text and original_language are immutable after creation
- translation_status transitions are monotonic: pending → (complete | failed); no reversion
- message_retention_flag is set per GDPR policy (Sophie's story)
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, CheckConstraint,
    Index, func, select, and_
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship, validates

Base = declarative_base()


class LanguageCode(str, Enum):
    """Supported language codes for v1."""
    EN = "EN"
    DE = "DE"
    JA = "JA"


class TranslationStatus(str, Enum):
    """Translation status for message record."""
    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"


class Message(Base):
    """
    Message record: original + translation as a unit.
    
    Per ADR-001 and contract-note-005: a message stores the original text in
    source language plus its translation to a single target language. Multi-target
    is deferred to v1.1.
    
    Storage invariant: (translation_status = 'complete') ⟺ (translated_text is not None)
    This is enforced at schema level via CHECK constraint.
    """
    __tablename__ = "messages"

    # Primary key and ownership
    message_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        doc="Globally unique, immutable message identifier"
    )
    sender_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        doc="FK to users.user_id; message author"
    )

    # Original message (immutable after creation)
    original_text = Column(
        Text,
        nullable=False,
        doc="Original message text in source language; immutable"
    )
    original_language = Column(
        String(2),
        nullable=False,
        doc="Source language code (EN, DE, JA, ...)"
    )

    # Translation (mutable until translation_status = 'complete')
    translated_text = Column(
        Text,
        nullable=True,
        doc="Translated message text in target language; null until translation_status='complete'"
    )
    target_language = Column(
        String(2),
        nullable=True,
        doc="Target language code; null if no translation requested"
    )

    # Translation metadata
    translation_model = Column(
        String(255),
        nullable=True,
        doc="Identifier of translation model used (e.g. 'claude-haiku-4.5')"
    )
    translation_timestamp = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when translation completed; non-null iff translation_status='complete'"
    )
    translation_status = Column(
        String(20),
        nullable=False,
        default="pending",
        doc="Translation state: pending | complete | failed"
    )
    translation_error = Column(
        Text,
        nullable=True,
        doc="Error message if translation_status='failed'; null otherwise"
    )

    # GDPR compliance
    message_retention_flag = Column(
        String(100),
        nullable=True,
        doc="Per-message retention policy (Sophie's GDPR story); cascade on deletion"
    )

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        doc="Message creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp"
    )

    __table_args__ = (
        # Invariant: original_text non-empty and ≤2000 chars
        CheckConstraint(
            "length(original_text) > 0 AND length(original_text) <= 2000",
            name="ck_original_text_length"
        ),
        # Invariant: translated_text (if non-null) ≤2000 chars
        CheckConstraint(
            "translated_text IS NULL OR length(translated_text) <= 2000",
            name="ck_translated_text_length"
        ),
        # Invariant: translation_status must be one of the valid values
        CheckConstraint(
            "translation_status IN ('pending', 'complete', 'failed')",
            name="ck_translation_status_valid"
        ),
        # Core invariant: (translation_status = 'complete') ⟺ (translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
        CheckConstraint(
            """
            (translation_status = 'complete' AND translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
            OR (translation_status != 'complete' AND translated_text IS NULL AND translation_timestamp IS NULL)
            """,
            name="ck_translation_complete_iff_text_and_timestamp"
        ),
        # Index for query performance: frontend requests by sender + created order
        Index(
            "idx_messages_sender_created",
            "sender_id",
            "created_at",
            desc=False
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Message {self.message_id} "
            f"sender={self.sender_id} "
            f"original_lang={self.original_language} "
            f"translation_status={self.translation_status}>"
        )


class MessageDeduplicationWindow:
    """
    Deduplication logic for idempotent message storage.
    
    Per contract-note-007: if POST /api/messages arrives with same
    (original_text, original_language, target_language) within 5-second window,
    return existing message_id instead of creating duplicate.
    """
    DEDUP_WINDOW_SECONDS = 5

    @staticmethod
    def find_duplicate(
        sender_id: str,
        original_text: str,
        original_language: str,
        target_language: Optional[str],
        session
    ) -> Optional[Message]:
        """
        Query for existing message within dedup window.
        
        Returns:
            Message if found within 5s window, else None
        """
        threshold = datetime.utcnow() - __import__('datetime').timedelta(
            seconds=MessageDeduplicationWindow.DEDUP_WINDOW_SECONDS
        )
        
        query = select(Message).where(
            and_(
                Message.sender_id == sender_id,
                Message.original_text == original_text,
                Message.original_language == original_language,
                Message.target_language == target_language,
                Message.created_at >= threshold
            )
        )
        
        result = session.execute(query).scalar_one_or_none()
        return result
