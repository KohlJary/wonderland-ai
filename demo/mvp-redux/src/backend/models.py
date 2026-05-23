"""SQLAlchemy models for the notebook app.

Core model: Note — represents a markdown note with title, body, tags (JSON array),
and server-managed timestamps.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def utc_now() -> datetime:
    """Return current UTC time as a timezone-aware datetime.
    
    Used as the default callable for timestamp columns.
    SQLAlchemy requires a Python callable that returns a datetime object,
    not func.now() which is SQL-side only.
    """
    return datetime.now(timezone.utc)





class Note(Base):
    """A markdown note with title, body, optional tags, and timestamps.

    Tags are stored as a JSON-serialized string array in the tags column.
    Timestamps (created_at, updated_at) are server-managed and immutable from
    the client side.

    Invariants:
    - A note always has exactly one id (primary key).
    - title and body are non-null strings (body can be empty).
    - tags defaults to an empty array []; each tag is a non-empty string.
    - created_at is immutable once set (server-set on creation).
    - updated_at is auto-updated on every write (including creation).
    """

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False, default="")
    tags = Column(Text, nullable=False, default="[]")  # JSON array as string
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: utc_now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: utc_now(),
        onupdate=lambda: utc_now(),
    )

    # Indexes for common query patterns
    __table_args__ = (
        Index("ix_notes_created_at", "created_at"),
        Index("ix_notes_updated_at", "updated_at"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to API response shape."""
        # Parse tags from JSON string to list
        try:
            tags_list = json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            tags_list = []

        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "tags": tags_list,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def tags_to_json(tags: list[str] | None) -> str:
        """Convert a list of tags to JSON string for storage."""
        if tags is None:
            return "[]"
        return json.dumps(tags)
