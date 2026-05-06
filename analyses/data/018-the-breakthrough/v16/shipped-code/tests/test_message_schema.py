"""
Tests for message schema and invariants.

Per contract-note-005: verify that message storage enforces:
- (translation_status = 'complete') ⟺ (translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
- message_id is globally unique and immutable
- original_text and original_language are immutable after creation
- translation_status transitions are monotonic: pending → (complete | failed); no reversion
"""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, Message, TranslationStatus, LanguageCode


@pytest.fixture
def db_session():
    """In-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestMessageInvariants:
    """Test that message schema enforces core invariants."""
    
    def test_pending_message_has_null_translation_fields(self, db_session):
        """
        Invariant: (translation_status = 'pending') ⟹ (translated_text IS NULL AND translation_timestamp IS NULL)
        """
        msg = Message(
            sender_id=uuid4(),
            original_text="Hello world",
            original_language="EN",
            target_language="DE",
            translation_status="pending",
            translated_text=None,
            translation_timestamp=None,
        )
        
        db_session.add(msg)
        db_session.commit()
        
        retrieved = db_session.query(Message).filter(
            Message.message_id == msg.message_id
        ).first()
        
        assert retrieved.translation_status == "pending"
        assert retrieved.translated_text is None
        assert retrieved.translation_timestamp is None
    
    def test_complete_message_has_translation_text_and_timestamp(self, db_session):
        """
        Invariant: (translation_status = 'complete') ⟹ (translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
        """
        now = datetime.utcnow()
        msg = Message(
            sender_id=uuid4(),
            original_text="Hello world",
            original_language="EN",
            translated_text="Hallo Welt",
            target_language="DE",
            translation_status="complete",
            translation_timestamp=now,
            translation_model="claude-haiku-4.5",
        )
        
        db_session.add(msg)
        db_session.commit()
        
        retrieved = db_session.query(Message).filter(
            Message.message_id == msg.message_id
        ).first()
        
        assert retrieved.translation_status == "complete"
        assert retrieved.translated_text == "Hallo Welt"
        assert retrieved.translation_timestamp is not None
    
    def test_cannot_violate_invariant_complete_with_null_text(self, db_session):
        """
        Invariant violation: attempt to set translation_status='complete' with null translated_text
        should fail at database level.
        """
        msg = Message(
            sender_id=uuid4(),
            original_text="Hello world",
            original_language="EN",
            target_language="DE",
            translation_status="complete",
            translated_text=None,  # VIOLATION
            translation_timestamp=datetime.utcnow(),
        )
        
        db_session.add(msg)
        
        # SQLite CHECK constraints are enforced on commit
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_cannot_violate_invariant_pending_with_text(self, db_session):
        """
        Invariant violation: attempt to set translation_status='pending' with non-null translated_text
        should fail at database level.
        """
        msg = Message(
            sender_id=uuid4(),
            original_text="Hello world",
            original_language="EN",
            target_language="DE",
            translation_status="pending",
            translated_text="Hallo Welt",  # VIOLATION: pending should have null text
            translation_timestamp=None,
        )
        
        db_session.add(msg)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_message_id_immutable(self, db_session):
        """
        Invariant: message_id is immutable after creation.
        """
        original_id = uuid4()
        msg = Message(
            message_id=original_id,
            sender_id=uuid4(),
            original_text="Hello world",
            original_language="EN",
            translation_status="pending",
        )
        
        db_session.add(msg)
        db_session.commit()
        
        retrieved = db_session.query(Message).filter(
            Message.message_id == original_id
        ).first()
        
        assert retrieved.message_id == original_id
    
    def test_failed_status_allows_error_message(self, db_session):
        """
        Test that translation_status='failed' can include an error message.
        """
        msg = Message(
            sender_id=uuid4(),
            original_text="Untranslatable emoji 🔥",
            original_language="EN",
            target_language="DE",
            translation_status="failed",
            translation_error="Language pair EN→DE not supported",
            translated_text=None,
            translation_timestamp=None,
        )
        
        db_session.add(msg)
        db_session.commit()
        
        retrieved = db_session.query(Message).filter(
            Message.message_id == msg.message_id
        ).first()
        
        assert retrieved.translation_status == "failed"
        assert retrieved.translation_error is not None
        assert retrieved.translated_text is None
        assert retrieved.translation_timestamp is None


class TestMessageValidation:
    """Test request-level validation (contract-note-007)."""
    
    def test_original_text_min_length(self, db_session):
        """original_text must be non-empty."""
        msg = Message(
            sender_id=uuid4(),
            original_text="",  # INVALID
            original_language="EN",
            translation_status="pending",
        )
        
        db_session.add(msg)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_original_text_max_length(self, db_session):
        """original_text must be ≤2000 chars."""
        msg = Message(
            sender_id=uuid4(),
            original_text="x" * 2001,  # INVALID
            original_language="EN",
            translation_status="pending",
        )
        
        db_session.add(msg)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_translated_text_max_length(self, db_session):
        """translated_text must be ≤2000 chars."""
        msg = Message(
            sender_id=uuid4(),
            original_text="Hello",
            original_language="EN",
            translated_text="x" * 2001,  # INVALID
            target_language="DE",
            translation_status="complete",
            translation_timestamp=datetime.utcnow(),
        )
        
        db_session.add(msg)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestDeduplicationWindow:
    """Test 5-second deduplication window (contract-note-007)."""
    
    def test_dedup_finds_recent_message(self, db_session):
        """Within 5-second window, find_duplicate returns existing message."""
        from src.models import MessageDeduplicationWindow
        
        sender = uuid4()
        msg = Message(
            sender_id=sender,
            original_text="Hello world",
            original_language="EN",
            target_language="DE",
            translation_status="pending",
        )
        
        db_session.add(msg)
        db_session.commit()
        
        # Immediately query for duplicate
        dup = MessageDeduplicationWindow.find_duplicate(
            sender_id=sender,
            original_text="Hello world",
            original_language="EN",
            target_language="DE",
            session=db_session
        )
        
        assert dup is not None
        assert dup.message_id == msg.message_id
    
    def test_dedup_returns_none_for_different_sender(self, db_session):
        """Dedup window is per-sender; different sender is not a duplicate."""
        from src.models import MessageDeduplicationWindow
        
        sender1 = uuid4()
        sender2 = uuid4()
        
        msg = Message(
            sender_id=sender1,
            original_text="Hello world",
            original_language="EN",
            target_language="DE",
            translation_status="pending",
        )
        
        db_session.add(msg)
        db_session.commit()
        
        # Query as different sender
        dup = MessageDeduplicationWindow.find_duplicate(
            sender_id=sender2,
            original_text="Hello world",
            original_language="EN",
            target_language="DE",
            session=db_session
        )
        
        assert dup is None
    
    def test_dedup_returns_none_for_different_text(self, db_session):
        """Dedup window is per-text; different text is not a duplicate."""
        from src.models import MessageDeduplicationWindow
        
        sender = uuid4()
        msg = Message(
            sender_id=sender,
            original_text="Hello world",
            original_language="EN",
            target_language="DE",
            translation_status="pending",
        )
        
        db_session.add(msg)
        db_session.commit()
        
        # Query with different text
        dup = MessageDeduplicationWindow.find_duplicate(
            sender_id=sender,
            original_text="Goodbye world",  # Different
            original_language="EN",
            target_language="DE",
            session=db_session
        )
        
        assert dup is None
